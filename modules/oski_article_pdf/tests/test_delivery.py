import base64
from unittest.mock import patch

from odoo.tests import TransactionCase, tagged


class _FakeSMTPSession:
    """Session SMTP factice : reproduit le pattern officiel Odoo
    (odoo/addons/base/tests/common.py::MockSmtplibCase.mock_smtplib_connection)
    pour permettre à mail.mail._send() d'aller jusqu'au bout et de marquer
    l'email 'sent', sans jamais toucher un vrai réseau."""

    def quit(self):
        pass

    def send_message(self, message, smtp_from, smtp_to_list):
        pass

    def set_debuglevel(self, level):
        pass

    def ehlo_or_helo_if_needed(self):
        pass

    def login(self, user, password):
        pass

    def starttls(self, keyfile=None, certfile=None, context=None):
        pass


@tagged('post_install', '-at_install')
class TestDelivery(TransactionCase):
    def setUp(self):
        super().setUp()
        blog = self.env['blog.blog'].create({'name': 'Développement Odoo'})
        self.post = self.env['blog.post'].create({
            'name': 'Article', 'blog_id': blog.id,
            'content': '<p>x</p>', 'is_published': True})
        self.post.oski_pdf_attachment_id = self.env['ir.attachment'].create({
            'name': 'g.pdf', 'datas': base64.b64encode(b'%PDF'),
            'mimetype': 'application/pdf', 'public': False})

    def _mails_to(self, email):
        return self.env['mail.mail'].sudo().search([('email_to', 'like', email)])

    def test_capture_sends_delivery_mail(self):
        self.env['oski.lead.capture'].sudo()._oski_capture_lead(
            'nouveau@example.com', True, 'pdf', self.post)
        self.assertTrue(self._mails_to('nouveau@example.com'),
                        "un email de livraison doit partir")

    def test_delivery_mail_contains_tokenized_link(self):
        self.env['oski.lead.capture'].sudo()._oski_capture_lead(
            'jeton@example.com', True, 'pdf', self.post)
        body = self._mails_to('jeton@example.com')[0].body_html or ''
        self.assertIn('access_token=', body)

    def test_delivery_mail_actually_sent(self):
        """Exigence propriétaire : ne pas se contenter de vérifier la
        création d'un mail.mail — vérifier qu'il est réellement parti
        (state == 'sent'), sinon l'assertion serait un théâtre de test.

        Odoo neutralise l'envoi réel pendant les tests
        (ir.mail_server._disable_send() -> True), donc un mail.mail reste
        'outgoing' même avec force_send=True. On reproduit ici le mock
        officiel d'Odoo (mock_smtplib_connection) : on désactive ce
        garde-fou et on intercepte smtplib au plus bas niveau, pour
        vérifier le comportement réel de bout en bout sans réseau."""
        IrMailServer = type(self.env['ir.mail_server'])
        fake_session = _FakeSMTPSession()
        with patch('smtplib.SMTP', side_effect=lambda *a, **kw: fake_session), \
             patch('smtplib.SMTP_SSL', side_effect=lambda *a, **kw: fake_session), \
             patch.object(IrMailServer, '_disable_send', lambda cls: False):
            self.env['oski.lead.capture'].sudo()._oski_capture_lead(
                'envoye@example.com', True, 'pdf', self.post)
        mail = self._mails_to('envoye@example.com')
        self.assertTrue(mail)
        self.assertEqual(mail[0].state, 'sent',
                          "le mail doit être réellement envoyé (force_send), "
                          "pas seulement mis en file")

    def test_existing_subscriber_still_gets_pdf(self):
        first = self.env['oski.lead.capture'].sudo()._oski_capture_lead(
            'connu@example.com', True, 'pdf', self.post)
        second = self.env['oski.lead.capture'].sudo()._oski_capture_lead(
            'connu@example.com', True, 'pdf', self.post)
        self.assertTrue(second['pdf_url'], "l'inscrit connu reçoit quand même son PDF")
        self.assertTrue(first['ok'] and second['ok'])

    def test_existing_subscriber_not_duplicated(self):
        for _ in range(2):
            self.env['oski.lead.capture'].sudo()._oski_capture_lead(
                'unique@example.com', True, 'pdf', self.post)
        contacts = self.env['mailing.contact'].sudo().search(
            [('email', '=ilike', 'unique@example.com')])
        self.assertEqual(len(contacts), 1)

    def test_no_mail_without_pdf(self):
        self.post.oski_pdf_attachment_id = False
        self.env['oski.lead.capture'].sudo()._oski_capture_lead(
            'sanspdf@example.com', True, 'pdf', self.post)
        self.assertFalse(self._mails_to('sanspdf@example.com'))

    def test_mail_failure_does_not_break_pdf_url(self):
        """Le téléchargement immédiat est la promesse principale : un échec
        d'envoi email ne doit jamais empêcher de renvoyer un pdf_url
        exploitable à l'appelant. On ne fait échouer QUE le template de
        livraison du guide PDF (pas l'offre de bienvenue, qui est un envoi
        indépendant du module amont)."""
        MailTemplate = self.env.registry['mail.template']
        original_send_mail = MailTemplate.send_mail
        target = self.env.ref('oski_article_pdf.mail_pdf_delivery', raise_if_not_found=False)
        target_id = target.id if target else None

        def _flaky_send_mail(tmpl_self, *args, **kwargs):
            if target_id and tmpl_self.id == target_id:
                raise Exception('smtp boom')
            return original_send_mail(tmpl_self, *args, **kwargs)

        with patch.object(MailTemplate, 'send_mail', _flaky_send_mail):
            res = self.env['oski.lead.capture'].sudo()._oski_capture_lead(
                'echec-mail@example.com', True, 'pdf', self.post)
        self.assertTrue(res['ok'])
        self.assertTrue(res['pdf_url'])
        self.assertIn('access_token=', res['pdf_url'])
        self.assertFalse(self._mails_to('echec-mail@example.com'))

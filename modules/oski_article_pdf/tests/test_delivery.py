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
        # FIX1 : le mail.mail est désormais créé/rendu EN REQUÊTE
        # (send_mail(force_send=False)) ; seul l'envoi SMTP proprement dit
        # est différé via mail.mail.send_after_commit(), qui envoie
        # immédiatement quand modules.module.current_test est actif (donc
        # ici, en test) — plus besoin de simuler un commit réel.
        self.env['oski.lead.capture'].sudo()._oski_capture_lead(
            'nouveau@example.com', True, 'pdf', self.post)
        self.assertTrue(self._mails_to('nouveau@example.com'),
                        "un email de livraison doit partir")

    def test_mail_record_persists_before_postcommit_runs(self):
        """FIX1 : le mail.mail (et son mail.message) doivent être créés EN
        REQUÊTE, pas uniquement au sein d'un callback cr.postcommit.

        Preuve dans le noyau : Cursor.commit() exécute postcommit.run() sur
        le curseur de requête encore ouvert (odoo/sql_db.py:555), puis la
        couche HTTP ferme ce même curseur (odoo/http.py:2270-2272), et
        Cursor._close() appelle rollback() (odoo/sql_db.py:536). Tout ce qui
        n'est écrit QUE depuis le callback post-commit est donc perdu dès
        que la requête se termine : la trace ne doit pas dépendre de
        l'exécution de postcommit.run() pour exister."""
        self.env['oski.lead.capture'].sudo()._oski_capture_lead(
            'trace@example.com', True, 'pdf', self.post)
        self.assertTrue(
            self._mails_to('trace@example.com'),
            "le mail.mail doit déjà exister avant tout postcommit.run() : "
            "sinon la trace ne survit jamais à la fermeture du curseur de "
            "la requête HTTP en production")

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
        vérifier le comportement réel de bout en bout sans réseau.

        FIX1 : mail.mail.send_after_commit() envoie immédiatement (self.send())
        quand modules.module.current_test est actif — donc ici, pendant
        _oski_capture_lead() elle-même — plus besoin de déclencher
        manuellement postcommit.run() ; les mocks smtplib doivent seulement
        rester actifs PENDANT cet appel."""
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
            # FIX1 : la création du mail.mail (send_mail) a lieu EN REQUÊTE,
            # donc l'échec se produit ici, directement dans
            # _oski_capture_lead() ; il doit rester sans effet sur le
            # pdf_url déjà calculé, et l'exception doit être avalée (loggée)
            # par le try/except de _oski_send_pdf_mail, jamais remontée.
            res = self.env['oski.lead.capture'].sudo()._oski_capture_lead(
                'echec-mail@example.com', True, 'pdf', self.post)
        self.assertTrue(res['ok'])
        self.assertTrue(res['pdf_url'])
        self.assertIn('access_token=', res['pdf_url'])
        self.assertFalse(self._mails_to('echec-mail@example.com'))

    def test_mail_send_deferred_to_postcommit_not_synchronous(self):
        """I3 : un SMTP qui pend ne doit jamais retarder la réponse de
        capture (et donc le téléchargement, qui n'attend que cette réponse).

        FIX1 : depuis mail.mail.send_after_commit(), l'envoi SMTP réel
        n'est déféré via cr.postcommit qu'EN DEHORS des tests — quand
        modules.module.current_test est actif (ce qui est TOUJOURS le cas
        pendant l'exécution normale de ce fichier), il envoie immédiatement
        pour ne pas dépendre d'un commit réel en test (voir
        odoo/addons/mail/models/mail_mail.py:668-688). Pour observer le
        comportement de PRODUCTION — où l'envoi ne doit PAS être
        synchrone —, on neutralise ce raccourci ici et on vérifie que
        mail.mail.send() n'est appelé qu'après avoir exécuté
        postcommit.run() (ce que fait le vrai commit() de la requête HTTP).

        La création/rendu du mail.mail (send_mail) reste, elle, synchrone
        depuis FIX1 (c'est tout l'objet de la correction) : seul l'envoi
        SMTP proprement dit (mail.mail.send()) doit rester différé."""
        MailMail = self.env.registry['mail.mail']
        with patch('odoo.modules.module.current_test', False), \
             patch.object(MailMail, 'send') as mocked_send:
            self.env['oski.lead.capture'].sudo()._oski_capture_lead(
                'differe@example.com', False, 'pdf', self.post)
            mocked_send.assert_not_called()
            self.env.cr.postcommit.run()
            mocked_send.assert_called_once()

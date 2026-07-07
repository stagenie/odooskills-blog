from odoo.tests import TransactionCase, tagged

MAIL_TEMPLATE = """Return-Path: <{email_from}>
From: Client Test <{email_from}>
To: {email_to}
Subject: {subject}
Date: Mon, 06 Jul 2026 10:00:00 +0000
Message-Id: {msg_id}
{extra}MIME-Version: 1.0
Content-Type: text/plain; charset=utf-8

Bonjour, ceci est un message de test.
"""


def process_raw(env, server, **kw):
    values = {
        'email_from': kw.get('email_from', 'client@example.com'),
        'email_to': kw.get('email_to', 'odooers@odooskills.com'),
        'subject': kw.get('subject', 'Question produit'),
        'msg_id': kw.get('msg_id', '<test-1@example.com>'),
        'extra': kw.get('extra', ''),
    }
    raw = MAIL_TEMPLATE.format(**values)
    return env['mail.thread'].with_context(
        default_fetchmail_server_id=server.id,
    ).message_process('oski.mail.inbox', raw)


@tagged('post_install', '-at_install')
class TestInboxRouting(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.box = cls.env['oski.mailbox'].create({
            'name': 'Odooers', 'email': 'odooers@odooskills.com',
            'imap_host': 'imap.test.local', 'imap_user': 'u',
            'imap_password': 'fake-test-password',
        })
        cls.server = cls.box.fetchmail_server_id
        cls.partner = cls.env['res.partner'].create({
            'name': 'Client Connu', 'email': 'connu@example.com'})

    def test_incoming_creates_record(self):
        rec_id = process_raw(self.env, self.server, msg_id='<t-new-1@example.com>')
        rec = self.env['oski.mail.inbox'].browse(rec_id)
        self.assertEqual(rec.mailbox_id, self.box)
        self.assertEqual(rec.subject, 'Question produit')
        self.assertIn('client@example.com', rec.email_from)
        self.assertIn('message de test', rec.body_html)
        self.assertEqual(rec.state, 'new')
        self.assertTrue(rec.date_received)

    def test_partner_matched(self):
        rec_id = process_raw(self.env, self.server,
                             email_from='connu@example.com',
                             msg_id='<t-partner-1@example.com>')
        rec = self.env['oski.mail.inbox'].browse(rec_id)
        self.assertEqual(rec.partner_id, self.partner)

    def test_dedup_message_id(self):
        process_raw(self.env, self.server, msg_id='<t-dup-1@example.com>')
        count_before = self.env['oski.mail.inbox'].search_count([])
        process_raw(self.env, self.server, msg_id='<t-dup-1@example.com>')
        self.assertEqual(self.env['oski.mail.inbox'].search_count([]), count_before,
                         "doublon créé malgré Message-Id identique")

    def test_reply_reopens_same_record(self):
        rec_id = process_raw(self.env, self.server, msg_id='<t-thread-1@example.com>')
        rec = self.env['oski.mail.inbox'].browse(rec_id)
        rec.state = 'done'
        msg = rec.message_ids[0]
        process_raw(self.env, self.server,
                    msg_id='<t-thread-2@example.com>',
                    subject='Re: Question produit',
                    extra='In-Reply-To: %s\nReferences: %s\n' % (
                        msg.message_id, msg.message_id))
        self.assertEqual(self.env['oski.mail.inbox'].search_count(
            [('id', '=', rec.id)]), 1)
        self.assertEqual(rec.state, 'new', "la re-réponse client doit repasser en Nouveau")
        self.assertEqual(self.env['oski.mail.inbox'].search_count([
            ('subject', 'like', 'Question produit')]), 1,
            "la réponse a créé une fiche au lieu de rejoindre le fil")

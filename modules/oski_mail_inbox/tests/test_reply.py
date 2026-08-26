from odoo.tests import TransactionCase, tagged

from .test_inbox_routing import process_raw


@tagged('post_install', '-at_install')
class TestReply(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.box = cls.env['oski.mailbox'].create({
            'name': 'Contact', 'email': 'tests-box@societe.example',
            'imap_host': 'imap.test.local', 'imap_user': 'u',
            'imap_password': 'fake-test-password',
        })
        rec_id = process_raw(cls.env, cls.box.fetchmail_server_id,
                             msg_id='<t-reply-1@example.com>')
        cls.record = cls.env['oski.mail.inbox'].browse(rec_id)

    def test_reply_from_is_mailbox(self):
        message = self.record.message_post(
            body='Merci pour votre message, voici la réponse.',
            message_type='comment',
            subtype_xmlid='mail.mt_comment',
            partner_ids=self.env['res.partner'].create(
                {'name': 'Client', 'email': 'client@example.com'}).ids,
        )
        self.assertIn('tests-box@societe.example', message.email_from,
                      "la réponse doit partir de l'adresse de la boîte")

    def test_reply_to_is_mailbox(self):
        reply_to = self.record._notify_get_reply_to()
        self.assertIn('tests-box@societe.example', reply_to[self.record.id])

    def test_comment_marks_answered(self):
        self.record.state = 'new'
        self.record.message_post(
            body='Réponse.', message_type='comment',
            subtype_xmlid='mail.mt_comment')
        self.assertEqual(self.record.state, 'answered')

    def test_internal_note_keeps_state(self):
        self.record.state = 'new'
        self.record.message_post(
            body='Note interne.', message_type='comment',
            subtype_xmlid='mail.mt_note')
        self.assertEqual(self.record.state, 'new',
                         "une note interne ne doit pas marquer Répondu")

    def test_incoming_email_keeps_state(self):
        # un message entrant (gateway) ne doit pas passer en Répondu
        self.record.state = 'new'
        process_raw(self.env, self.box.fetchmail_server_id,
                    msg_id='<t-reply-2@example.com>', subject='Autre question')
        self.assertEqual(self.record.state, 'new')

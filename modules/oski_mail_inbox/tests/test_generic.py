from odoo import fields
from odoo.tests import TransactionCase, tagged

from .test_inbox_routing import process_raw


@tagged('post_install', '-at_install')
class TestGenericV2(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.box = cls.env['oski.mailbox'].create({
            'name': 'Odooers', 'email': 'tests-box@odooskills.example',
            'imap_host': 'imap.test.local', 'imap_user': 'u',
            'imap_password': 'fake-test-password',
        })

    def test_incoming_stores_message_id(self):
        rec_id = process_raw(self.env, self.box.fetchmail_server_id,
                             msg_id='<t-gen-1@example.com>')
        rec = self.env['oski.mail.inbox'].browse(rec_id)
        self.assertEqual(rec.email_message_id, '<t-gen-1@example.com>',
                         "sans Message-ID stocké, aucun geste distant n'est possible")

    def test_reply_keeps_original_message_id(self):
        rec_id = process_raw(self.env, self.box.fetchmail_server_id,
                             msg_id='<t-gen-2@example.com>')
        rec = self.env['oski.mail.inbox'].browse(rec_id)
        msg = rec.message_ids[0]
        process_raw(self.env, self.box.fetchmail_server_id,
                    msg_id='<t-gen-3@example.com>',
                    subject='Re: Question produit',
                    extra='In-Reply-To: %s\nReferences: %s\n' % (
                        msg.message_id, msg.message_id))
        self.assertEqual(rec.email_message_id, '<t-gen-2@example.com>',
                         "la relance ne doit pas écraser la clé du message d'origine")

    def test_reply_reactivates_archived_record(self):
        rec_id = process_raw(self.env, self.box.fetchmail_server_id,
                             msg_id='<t-gen-5@example.com>')
        rec = self.env['oski.mail.inbox'].browse(rec_id)
        rec.write({'state': 'done', 'active': False})
        msg = rec.message_ids[0]
        process_raw(self.env, self.box.fetchmail_server_id,
                    msg_id='<t-gen-6@example.com>',
                    subject='Re: Question produit',
                    extra='In-Reply-To: %s\nReferences: %s\n' % (
                        msg.message_id, msg.message_id))
        self.assertTrue(rec.active,
                        "une relance doit rouvrir un fil archivé : la conversation reprend")
        self.assertEqual(rec.state, 'new')

    def test_reply_to_spam_stays_archived_and_spam(self):
        rec_id = process_raw(self.env, self.box.fetchmail_server_id,
                             msg_id='<t-gen-7@example.com>')
        rec = self.env['oski.mail.inbox'].browse(rec_id)
        rec.write({'state': 'spam', 'active': False})
        msg = rec.message_ids[0]
        process_raw(self.env, self.box.fetchmail_server_id,
                    msg_id='<t-gen-8@example.com>',
                    subject='Re: Question produit',
                    extra='In-Reply-To: %s\nReferences: %s\n' % (
                        msg.message_id, msg.message_id))
        self.assertFalse(rec.active,
                         "un fil indésirable ne doit pas se ranimer tout seul")
        self.assertEqual(rec.state, 'spam',
                         "une relance ne doit pas sortir un fil de l'état indésirable")

    def test_record_is_archivable(self):
        rec_id = process_raw(self.env, self.box.fetchmail_server_id,
                             msg_id='<t-gen-4@example.com>')
        rec = self.env['oski.mail.inbox'].browse(rec_id)
        self.assertTrue(rec.active)
        rec.active = False
        self.assertFalse(self.env['oski.mail.inbox'].search([('id', '=', rec.id)]),
                         "une fiche archivée doit sortir des recherches par défaut")
        self.assertTrue(rec.exists(), "archiver ne doit jamais détruire la fiche")

    def test_spam_state_exists(self):
        states = dict(self.env['oski.mail.inbox']._fields['state'].selection)
        self.assertIn('spam', states)

    def test_backlog_since_defaults_to_current_year(self):
        box = self.env['oski.mailbox'].create(
            {'name': 'Neuve', 'email': 'tests-neuve@odooskills.example'})
        self.assertEqual(box.backlog_since,
                         fields.Date.to_date('%d-01-01' % fields.Date.today().year),
                         "la date par défaut ne doit pas être une année figée en dur")

    def test_no_hardcoded_mailboxes(self):
        self.assertFalse(
            self.env['ir.model.data'].search([
                ('module', '=', 'oski_mail_inbox'),
                ('model', '=', 'oski.mailbox'),
            ]),
            "le module ne doit plus livrer de boîte en dur : il est destiné au store")

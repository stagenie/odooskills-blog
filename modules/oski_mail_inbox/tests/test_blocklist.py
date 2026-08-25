from unittest.mock import patch

from odoo.exceptions import AccessError
from odoo.tests import TransactionCase, tagged

from .test_imap_layer import FakeImapServer
from .test_inbox_routing import process_raw


@tagged('post_install', '-at_install')
class TestBlocklist(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.box = cls.env['oski.mailbox'].create({
            'name': 'Odooers', 'email': 'tests-block@odooskills.example',
            'imap_host': 'imap.test.local', 'imap_user': 'u',
            'imap_password': 'fake-test-password',
        })
        cls.user = cls.env['res.users'].create({
            'name': 'Agent Messagerie', 'login': 'block_user',
            'group_ids': [(6, 0, [
                cls.env.ref('base.group_user').id,
                cls.env.ref('oski_mail_inbox.group_user').id])],
        })
        cls.manager = cls.env['res.users'].create({
            'name': 'Manager Messagerie', 'login': 'block_manager',
            'group_ids': [(6, 0, [
                cls.env.ref('base.group_user').id,
                cls.env.ref('oski_mail_inbox.group_manager').id])],
        })

    def test_spam_records_the_sender(self):
        rec_id = process_raw(self.env, self.box.fetchmail_server_id,
                             email_from='indesirable@example.com',
                             msg_id='<t-bl-1@example.com>')
        record = self.env['oski.mail.inbox'].browse(rec_id)
        fake = FakeImapServer(capabilities=('IMAP4REV1', 'MOVE'))
        with patch.object(type(self.box), '_imap_connect', return_value=fake):
            record.action_mark_spam()
        self.assertTrue(
            self.env['oski.mail.blocklist'].search([
                ('email', '=', 'indesirable@example.com')]),
            "marquer indésirable sans mémoire ferait revenir le même expéditeur demain")

    def test_email_is_normalised(self):
        entry = self.env['oski.mail.blocklist'].create(
            {'email': '  SPAMMEUR@Example.COM '})
        self.assertEqual(entry.email, 'spammeur@example.com',
                         "sans normalisation, la contrainte d'unicité laisse passer les doublons")

    def test_blocked_sender_lands_in_spam(self):
        self.env['oski.mail.blocklist'].create({'email': 'bloque@example.com'})
        fake = FakeImapServer(capabilities=('IMAP4REV1', 'MOVE'))
        with patch.object(type(self.box), '_imap_connect', return_value=fake):
            rec_id = process_raw(self.env, self.box.fetchmail_server_id,
                                 email_from='bloque@example.com',
                                 msg_id='<t-bl-2@example.com>')
            record = self.env['oski.mail.inbox'].browse(rec_id)
        self.assertEqual(record.state, 'spam')
        self.assertFalse(record.active)

    def test_gateway_does_not_connect_imap(self):
        self.env['oski.mail.blocklist'].create({'email': 'bloque2@example.com'})
        with patch.object(type(self.box), '_imap_connect') as connect:
            process_raw(self.env, self.box.fetchmail_server_id,
                        email_from='bloque2@example.com',
                        msg_id='<t-bl-3@example.com>')
        self.assertEqual(connect.call_count, 0,
                         "la relève entrante ne doit jamais ouvrir une connexion IMAP en synchrone")
        self.assertTrue(
            self.env['oski.mail.imap.action'].search([
                ('email_message_id', '=', '<t-bl-3@example.com>')]),
            "elle doit empiler l'action au lieu de l'exécuter")

    def test_reblock_after_unblock_reuses_the_row(self):
        entry = self.env['oski.mail.blocklist'].create({'email': 'yo-yo@example.com'})
        entry.active = False
        again = self.env['oski.mail.blocklist']._block('yo-yo@example.com')
        self.assertEqual(again, entry,
                         "recréer heurterait la contrainte UNIQUE sur la ligne archivée")
        self.assertTrue(again.active)

    def test_user_can_block(self):
        self.env['oski.mail.blocklist'].with_user(self.user).create(
            {'email': 'gene@example.com'})

    def test_user_cannot_unblock(self):
        entry = self.env['oski.mail.blocklist'].create({'email': 'tenace@example.com'})
        with self.assertRaises(AccessError):
            entry.with_user(self.user).write({'active': False})

    def test_manager_can_unblock(self):
        entry = self.env['oski.mail.blocklist'].create({'email': 'pardonne@example.com'})
        entry.with_user(self.manager).write({'active': False})
        self.assertFalse(entry.active)

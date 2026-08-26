from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestMailbox(TransactionCase):

    def _mailbox_vals(self, email='tests-mbox@societe.example'):
        return {
            'name': 'Contact',
            'email': email,
            'imap_host': 'imap.test.local',
            'imap_port': 993,
            'imap_ssl': True,
            'imap_user': email,
            'imap_password': 'fake-test-password',
        }

    def test_create_syncs_fetchmail_server(self):
        box = self.env['oski.mailbox'].create(self._mailbox_vals())
        server = box.fetchmail_server_id
        self.assertTrue(server, "fetchmail.server non créé")
        self.assertEqual(server.server, 'imap.test.local')
        self.assertEqual(server.port, 993)
        self.assertTrue(server.is_ssl)
        self.assertEqual(server.server_type, 'imap')
        self.assertEqual(server.user, 'tests-mbox@societe.example')
        self.assertEqual(server.object_id.model, 'oski.mail.inbox')

    def test_write_updates_server(self):
        box = self.env['oski.mailbox'].create(self._mailbox_vals())
        box.write({'imap_host': 'imap2.test.local', 'imap_port': 143, 'imap_ssl': False})
        self.assertEqual(box.fetchmail_server_id.server, 'imap2.test.local')
        self.assertEqual(box.fetchmail_server_id.port, 143)
        self.assertFalse(box.fetchmail_server_id.is_ssl)

    def test_no_server_without_credentials(self):
        box = self.env['oski.mailbox'].create(
            {'name': 'Info', 'email': 'tests-info@societe.example'})
        self.assertFalse(box.fetchmail_server_id, "serveur créé sans credentials IMAP")

    def test_unlink_removes_server(self):
        box = self.env['oski.mailbox'].create(self._mailbox_vals())
        server_id = box.fetchmail_server_id.id
        box.unlink()
        self.assertFalse(self.env['fetchmail.server'].browse(server_id).exists())

    def test_email_unique(self):
        self.env['oski.mailbox'].create(self._mailbox_vals())
        with self.assertRaises(Exception):
            with self.env.cr.savepoint():
                self.env['oski.mailbox'].create(self._mailbox_vals())

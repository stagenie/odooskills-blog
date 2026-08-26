from odoo.exceptions import AccessError
from odoo.tests import TransactionCase, tagged

from .test_inbox_routing import process_raw


@tagged('post_install', '-at_install')
class TestSecurity(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.box = cls.env['oski.mailbox'].create({
            'name': 'Contact', 'email': 'tests-box@societe.example',
            'imap_host': 'imap.test.local', 'imap_user': 'u',
            'imap_password': 'fake-test-password',
        })
        rec_id = process_raw(cls.env, cls.box.fetchmail_server_id,
                             msg_id='<t-sec-1@example.com>')
        cls.record = cls.env['oski.mail.inbox'].browse(rec_id)
        cls.user = cls.env['res.users'].create({
            'name': 'Lecteur Messagerie', 'login': 'inbox_user',
            'group_ids': [(6, 0, [
                cls.env.ref('base.group_user').id,
                cls.env.ref('oski_mail_inbox.group_user').id])],
        })
        cls.manager = cls.env['res.users'].create({
            'name': 'Manager Messagerie', 'login': 'inbox_manager',
            'group_ids': [(6, 0, [
                cls.env.ref('base.group_user').id,
                cls.env.ref('oski_mail_inbox.group_manager').id])],
        })

    def test_user_reads_and_updates_state(self):
        rec = self.record.with_user(self.user)
        self.assertEqual(rec.subject, 'Question produit')
        rec.action_mark_done()
        self.assertEqual(rec.state, 'done')

    def test_user_cannot_create_mailbox(self):
        with self.assertRaises(AccessError):
            self.env['oski.mailbox'].with_user(self.user).create({
                'name': 'Pirate', 'email': 'pirate@societe.example'})

    def test_user_cannot_unlink_record(self):
        with self.assertRaises(AccessError):
            self.record.with_user(self.user).unlink()

    def test_user_can_create_inbox_record_but_not_unlink_it(self):
        # groundwork pour le message neuf (Tâche 5) : la fiche qui porte le
        # fil d'un message composé par l'utilisateur doit pouvoir naître sous
        # son propre uid, sans passer par le manager.
        record = self.env['oski.mail.inbox'].with_user(self.user).create({
            'subject': 'Créé par un utilisateur', 'mailbox_id': self.box.id})
        self.assertTrue(record)
        with self.assertRaises(AccessError):
            record.with_user(self.user).unlink()

    def test_manager_crud_mailbox(self):
        box = self.env['oski.mailbox'].with_user(self.manager).create({
            'name': 'Info', 'email': 'info-sec-test@societe.example'})
        box.write({'name': 'Info 2'})
        box.unlink()

    def test_password_hidden_from_non_system(self):
        with self.assertRaises(AccessError):
            self.box.with_user(self.manager).read(['imap_password'])

    def test_mail_server_hidden_from_non_system(self):
        # même restriction que imap_password, pour la même raison : un
        # Manager Messagerie n'est pas forcément administrateur système, et
        # ir.mail_server n'est lisible que par base.group_system.
        with self.assertRaises(AccessError):
            self.box.with_user(self.manager).read(['mail_server_id'])

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

    def test_fallback_normalised_address_is_still_recognised(self):
        # 'email_normalize' refuse une entrée sans arobase ; le secours
        # .strip().lower() prend le relais. Si le stockage et la recherche
        # ne normalisaient pas de la même façon, la ligne créée ici
        # afficherait un blocage qui ne bloquerait jamais rien.
        self.env['oski.mail.blocklist'].create({'email': '  Malformed Entry  '})
        self.assertTrue(
            self.env['oski.mail.blocklist']._is_blocked('  Malformed Entry  '),
            "le stockage et la recherche doivent utiliser la même normalisation")

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

    def test_reply_from_blocked_sender_does_not_revive_thread(self):
        # L'expéditeur est bloqué APRÈS le premier message : le fil existait
        # déjà, non-spam. La relance ne doit pas le ramener en tête de boîte.
        rec_id = process_raw(self.env, self.box.fetchmail_server_id,
                             email_from='latent@example.com',
                             msg_id='<t-bl-latent-1@example.com>')
        record = self.env['oski.mail.inbox'].browse(rec_id)
        record.state = 'done'
        self.env['oski.mail.blocklist'].create({'email': 'latent@example.com'})
        msg = record.message_ids[0]
        process_raw(self.env, self.box.fetchmail_server_id,
                    email_from='latent@example.com',
                    msg_id='<t-bl-latent-2@example.com>',
                    subject='Re: Question produit',
                    extra='In-Reply-To: %s\nReferences: %s\n' % (
                        msg.message_id, msg.message_id))
        self.assertEqual(record.state, 'spam',
                         "un expéditeur bloqué entre-temps ne doit pas rouvrir le fil")
        self.assertFalse(record.active)

    def test_own_mailbox_is_never_blocked(self):
        rec_id = process_raw(self.env, self.box.fetchmail_server_id,
                             email_from=self.box.email,
                             msg_id='<t-bl-own-1@example.com>')
        record = self.env['oski.mail.inbox'].browse(rec_id)
        fake = FakeImapServer(capabilities=('IMAP4REV1', 'MOVE'))
        with patch.object(type(self.box), '_imap_connect', return_value=fake):
            record.action_mark_spam()
        self.assertFalse(
            self.env['oski.mail.blocklist'].search([('email', '=', self.box.email)]),
            "bloquer sa propre boîte couperait le module de sa propre adresse, sans recours")
        self.assertEqual(record.state, 'spam',
                         "le déplacement en indésirable reste dû, seule la mémorisation est sautée")

    def test_reblock_after_unblock_reuses_the_row(self):
        entry = self.env['oski.mail.blocklist'].create({'email': 'yo-yo@example.com'})
        entry.active = False
        again = self.env['oski.mail.blocklist']._block('yo-yo@example.com')
        self.assertEqual(again, entry,
                         "recréer heurterait la contrainte UNIQUE sur la ligne archivée")
        self.assertTrue(again.active)

    def test_reblock_refreshes_provenance(self):
        first_id = process_raw(self.env, self.box.fetchmail_server_id,
                               email_from='revenant@example.com',
                               msg_id='<t-bl-revenant-1@example.com>')
        first_record = self.env['oski.mail.inbox'].browse(first_id)
        entry = self.env['oski.mail.blocklist'].with_user(self.user)._block(
            'revenant@example.com', origin_inbox=first_record)
        entry.with_user(self.manager).write({'active': False})
        second_id = process_raw(self.env, self.box.fetchmail_server_id,
                                email_from='revenant@example.com',
                                msg_id='<t-bl-revenant-2@example.com>')
        second_record = self.env['oski.mail.inbox'].browse(second_id)
        again = self.env['oski.mail.blocklist'].with_user(self.manager)._block(
            'revenant@example.com', origin_inbox=second_record)
        self.assertEqual(again, entry)
        self.assertEqual(again.origin_inbox_id, second_record,
                         "la ré-activation doit décrire le dernier blocage, pas le premier")
        self.assertEqual(again.blocked_uid, self.manager,
                         "sans mise à jour, l'audit montrerait le mauvais responsable")

    def test_user_can_block(self):
        entry = self.env['oski.mail.blocklist'].with_user(self.user).create(
            {'email': 'gene@example.com'})
        self.assertEqual(entry.blocked_uid, self.user)
        self.assertTrue(entry.active)

    def test_user_cannot_unblock(self):
        entry = self.env['oski.mail.blocklist'].create({'email': 'tenace@example.com'})
        with self.assertRaisesRegex(AccessError, 'not allowed to modify'):
            entry.with_user(self.user).write({'active': False})

    def test_manager_can_unblock(self):
        entry = self.env['oski.mail.blocklist'].create({'email': 'pardonne@example.com'})
        entry.with_user(self.manager).write({'active': False})
        self.assertFalse(entry.active)

    def test_unblock_lets_mail_through_again(self):
        entry = self.env['oski.mail.blocklist'].create({'email': 'gracie@example.com'})
        entry.with_user(self.manager).write({'active': False})
        rec_id = process_raw(self.env, self.box.fetchmail_server_id,
                             email_from='gracie@example.com',
                             msg_id='<t-bl-gracie-1@example.com>')
        record = self.env['oski.mail.inbox'].browse(rec_id)
        self.assertEqual(record.state, 'new',
                         "un stray active_test=False garderait cette adresse bloquée à jamais")
        self.assertTrue(record.active)

from unittest.mock import patch

from odoo.exceptions import AccessError
from odoo.tests import TransactionCase, tagged

from .test_imap_layer import FakeImapServer
from .test_inbox_routing import process_raw

QUEUE_LOGGER = 'odoo.addons.oski_mail_inbox.models.oski_mail_imap_action'


@tagged('post_install', '-at_install')
class TestImapActions(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.box = cls.env['oski.mailbox'].create({
            'name': 'Odooers', 'email': 'tests-act@odooskills.example',
            'imap_host': 'imap.test.local', 'imap_user': 'u',
            'imap_password': 'fake-test-password',
        })

    def _record(self, msg_id):
        rec_id = process_raw(self.env, self.box.fetchmail_server_id, msg_id=msg_id)
        return self.env['oski.mail.inbox'].browse(rec_id)

    def _with_fake(self, fake):
        return patch.object(type(self.box), '_imap_connect', return_value=fake)

    def _with_unreachable(self):
        """Panne de connexion : lève ET journalise, pour que l'assertion sur
        le log serve de preuve plutôt que de laisser un WARNING silencieux."""
        return patch.object(type(self.box), '_imap_connect',
                             side_effect=OSError('serveur injoignable'))

    def test_delete_archives_and_moves(self):
        record = self._record('<t-act-1@example.com>')
        fake = FakeImapServer(capabilities=('IMAP4REV1', 'MOVE'))
        with self._with_fake(fake):
            record.action_delete_email()
        self.assertFalse(record.active, "la fiche doit être archivée, jamais détruite")
        self.assertTrue(record.exists())
        self.assertEqual(fake.moved_to, ['"INBOX.Trash"'])
        self.assertEqual(record.imap_action_ids.state, 'done')

    def test_spam_sets_state_and_moves_to_junk(self):
        record = self._record('<t-act-2@example.com>')
        fake = FakeImapServer(capabilities=('IMAP4REV1', 'MOVE'))
        with self._with_fake(fake):
            record.action_mark_spam()
        self.assertEqual(record.state, 'spam')
        self.assertFalse(record.active)
        self.assertEqual(fake.moved_to, ['"INBOX.Junk"'])

    def test_failure_queues_and_archives_anyway(self):
        record = self._record('<t-act-3@example.com>')
        with self._with_unreachable(), \
             self.assertLogs(QUEUE_LOGGER, level='WARNING') as log_catcher:
            record.action_delete_email()
        self.assertTrue(
            any('injoignable' in message for message in log_catcher.output),
            "la panne de connexion doit être journalisée, pas seulement absorbée")
        self.assertFalse(record.active,
                         "l'échec distant ne doit pas bloquer le geste dans Odoo")
        action = record.imap_action_ids
        self.assertEqual(action.state, 'pending')
        self.assertEqual(action.attempts, 1)
        self.assertIn('injoignable', action.last_error)
        self.assertTrue(record.imap_pending, "la fiche doit signaler la synchro en attente")
        self.assertFalse(record.imap_failed,
                         "un seul échec, loin du plafond, n'est pas un échec définitif")

    def test_cron_replays_and_succeeds(self):
        record = self._record('<t-act-4@example.com>')
        with self._with_unreachable(), self.assertLogs(QUEUE_LOGGER, level='WARNING'):
            record.action_delete_email()
        fake = FakeImapServer(capabilities=('IMAP4REV1', 'MOVE'))
        with self._with_fake(fake):
            self.env['oski.mail.imap.action']._cron_process_imap_actions()
        self.assertEqual(record.imap_action_ids.state, 'done')
        self.assertFalse(record.imap_pending)
        self.assertFalse(record.imap_failed)

    def test_cron_groups_one_connection_per_mailbox(self):
        records = [self._record('<t-act-grp-%d@example.com>' % i) for i in range(3)]
        with self._with_unreachable(), self.assertLogs(QUEUE_LOGGER, level='WARNING'):
            for record in records:
                record.action_delete_email()
        fake = FakeImapServer(capabilities=('IMAP4REV1', 'MOVE'))
        with patch.object(type(self.box), '_imap_connect', return_value=fake) as connect:
            self.env['oski.mail.imap.action']._cron_process_imap_actions()
        self.assertEqual(connect.call_count, 1,
                         "trois actions d'une même boîte = une seule connexion")
        self.assertEqual(len(fake.moved_to), 3)

    def test_attempts_cap_marks_failed(self):
        record = self._record('<t-act-5@example.com>')
        with self._with_unreachable(), self.assertLogs(QUEUE_LOGGER, level='WARNING'):
            record.action_delete_email()
            for _i in range(5):
                self.env['oski.mail.imap.action']._cron_process_imap_actions()
        self.assertEqual(record.imap_action_ids.state, 'failed')
        self.assertEqual(record.imap_action_ids.attempts, 5,
                         "le plafond doit arrêter la boucle à 5 tentatives, pas plus")
        self.assertTrue(record.imap_failed,
                        "une action au plafond est un échec définitif, pas une attente")
        # Un tick de cron supplémentaire ne doit plus toucher une action déjà
        # classée 'failed' : le cron ne recherche que 'pending'.
        self.env['oski.mail.imap.action']._cron_process_imap_actions()
        self.assertEqual(record.imap_action_ids.attempts, 5,
                         "une action en échec définitif ne doit plus être rejouée par le cron")

    def test_copied_not_purged_is_reported(self):
        record = self._record('<t-act-6@example.com>')
        fake = FakeImapServer(capabilities=('IMAP4REV1',))
        with self._with_fake(fake):
            record.action_delete_email()
        self.assertEqual(record.imap_action_ids.result, 'copied_not_purged',
                         "un serveur sans purge doit le dire, pas simuler un succès")

    def test_user_reads_queue_but_cannot_touch_it(self):
        user = self.env['res.users'].create({
            'name': 'Agent', 'login': 'queue_user',
            'group_ids': [(6, 0, [
                self.env.ref('base.group_user').id,
                self.env.ref('oski_mail_inbox.group_user').id])],
        })
        record = self._record('<t-act-acl@example.com>')
        with self._with_unreachable(), self.assertLogs(QUEUE_LOGGER, level='WARNING'):
            record.action_delete_email()
        action = record.imap_action_ids
        # lecture nécessaire : imap_pending se calcule sous l'identité du cliqueur
        action.with_user(user).read(['state'])
        with self.assertRaises(AccessError):
            action.with_user(user).write({'state': 'done'})
        with self.assertRaises(AccessError):
            action.with_user(user).unlink()

    def test_record_without_message_id_is_still_archived(self):
        record = self._record('<t-act-7@example.com>')
        record.email_message_id = False
        fake = FakeImapServer(capabilities=('IMAP4REV1', 'MOVE'))
        with self._with_fake(fake):
            record.action_delete_email()
        self.assertFalse(record.active)
        self.assertFalse(record.imap_action_ids,
                         "sans clé, aucune action distante n'est créée")
        self.assertTrue(
            any("n'a pas pu être déplacé" in (message.body or '')
                for message in record.message_ids),
            "l'absence de synchronisation distante doit laisser une trace sur la fiche, "
            "pas disparaître en silence")

    def test_gestures_as_ordinary_user(self):
        """Un utilisateur ordinaire peut supprimer et classer sans toucher au mot de
        passe IMAP — la file est créée et rejouée sous sudo() par le geste lui-même."""
        user = self.env['res.users'].create({
            'name': 'Agent', 'login': 'gesture_user',
            'group_ids': [(6, 0, [
                self.env.ref('base.group_user').id,
                self.env.ref('oski_mail_inbox.group_user').id])],
        })
        delete_record = self._record('<t-act-user-del@example.com>')
        spam_record = self._record('<t-act-user-spam@example.com>')
        fake = FakeImapServer(capabilities=('IMAP4REV1', 'MOVE'))
        with self._with_fake(fake):
            delete_record.with_user(user).action_delete_email()
            spam_record.with_user(user).action_mark_spam()
        self.assertFalse(delete_record.active)
        self.assertEqual(delete_record.imap_action_ids.state, 'done')
        self.assertEqual(spam_record.state, 'spam')
        self.assertFalse(spam_record.active)
        self.assertEqual(fake.moved_to, ['"INBOX.Trash"', '"INBOX.Junk"'])

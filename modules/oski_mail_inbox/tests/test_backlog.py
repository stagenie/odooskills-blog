from unittest.mock import patch

from odoo import fields
from odoo.tests import TransactionCase, tagged

RAW_TEMPLATE = (b"From: Client <client%d@example.com>\r\n"
                b"To: odooers@odooskills.com\r\n"
                b"Subject: Historique %d\r\n"
                b"Date: Mon, 02 Feb 2026 10:00:00 +0000\r\n"
                b"Message-Id: <backlog-%d@example.com>\r\n"
                b"MIME-Version: 1.0\r\n"
                b"Content-Type: text/plain; charset=utf-8\r\n\r\n"
                b"Message historique.\r\n")


class FakeImap:
    """Simule imaplib : 5 emails, UIDs 11..15."""

    def __init__(self):
        self.uids = list(range(11, 16))
        self.selected = None
        self.search_criteria = None

    def select(self, mailbox, readonly=False):
        self.selected = (mailbox, readonly)
        return 'OK', [b'5']

    def uid(self, command, *args):
        if command == 'search':
            self.search_criteria = args[-1]
            return 'OK', [' '.join(str(u) for u in self.uids).encode()]
        if command == 'fetch':
            n = int(args[0])
            return 'OK', [(b'11 (BODY[] {42}', RAW_TEMPLATE % (n, n, n)), b')']
        raise AssertionError('commande inattendue %s' % command)

    def logout(self):
        pass


@tagged('post_install', '-at_install')
class TestBacklog(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.box = cls.env['oski.mailbox'].create({
            'name': 'Odooers', 'email': 'tests-box@odooskills.example',
            'imap_host': 'imap.test.local', 'imap_user': 'u',
            'imap_password': 'fake-test-password',
            'backlog_since': fields.Date.to_date('2026-01-01'),
        })

    def _run_backlog(self, fake):
        with patch.object(type(self.box), '_imap_connect', return_value=fake):
            self.box.with_context(oski_backlog_no_commit=True)._process_backlog_batch()

    def test_since_criteria_english_months(self):
        crit = self.box._imap_since_criteria(fields.Date.to_date('2026-01-01'))
        self.assertEqual(crit, '(SINCE "01-Jan-2026")',
                         "SINCE doit utiliser les mois anglais quelle que soit la locale")

    def test_import_batch(self):
        fake = FakeImap()
        self.box.action_start_backlog()
        self.assertEqual(self.box.backlog_state, 'pending')
        self._run_backlog(fake)
        self.assertEqual(fake.selected, ('INBOX', True),
                         "INBOX doit être ouverte en lecture seule")
        self.assertEqual(
            self.env['oski.mail.inbox'].search_count(
                [('mailbox_id', '=', self.box.id)]), 5)
        self.assertEqual(self.box.backlog_last_uid, 15)
        self.assertEqual(self.box.backlog_done_count, 5)

    def test_import_resumes_and_finishes(self):
        fake = FakeImap()
        self.box.action_start_backlog()
        self._run_backlog(fake)
        # deuxième passe : plus rien de nouveau -> done, pas de doublon
        self._run_backlog(fake)
        self.assertEqual(self.box.backlog_state, 'done')
        self.assertEqual(
            self.env['oski.mail.inbox'].search_count(
                [('mailbox_id', '=', self.box.id)]), 5, "doublons créés à la reprise")

    def test_restart_after_done_no_duplicates(self):
        fake = FakeImap()
        self.box.action_start_backlog()
        self._run_backlog(fake)
        self._run_backlog(fake)
        self.box.action_start_backlog()  # relance volontaire
        self.assertEqual(self.box.backlog_last_uid, 0)
        self._run_backlog(fake)
        self.assertEqual(
            self.env['oski.mail.inbox'].search_count(
                [('mailbox_id', '=', self.box.id)]), 5,
            "la relance complète doit être absorbée par la dédup Message-Id")
        self.assertEqual(
            self.box.backlog_done_count, 5,
            "la progression compte les messages traités, pas les fiches créées : "
            "la dédup en écarte 5/5 ici, mais les 5 ont bien été traités par le "
            "gateway avant d'être écartés")

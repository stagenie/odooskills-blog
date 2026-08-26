from unittest.mock import patch

from odoo import fields
from odoo.tests import TransactionCase, tagged

from .test_backlog import FakeImap


@tagged('post_install', '-at_install')
class TestBacklogGauge(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.box = cls.env['oski.mailbox'].create({
            'name': 'Contact', 'email': 'tests-gauge@societe.example',
            'imap_host': 'imap.test.local', 'imap_user': 'u',
            'imap_password': 'fake-test-password',
            'backlog_since': fields.Date.to_date('2026-01-01'),
        })

    def _run(self, fake):
        with patch.object(type(self.box), '_imap_connect', return_value=fake):
            self.box.with_context(oski_backlog_no_commit=True)._process_backlog_batch()

    def test_total_is_recorded_on_first_batch(self):
        self.box.action_start_backlog()
        self._run(FakeImap())
        self.assertEqual(self.box.backlog_total_count, 5,
                         "sans dénominateur, la jauge n'a rien à afficher")

    def test_progress_reaches_one_hundred(self):
        self.box.action_start_backlog()
        self._run(FakeImap())
        self.assertEqual(self.box.backlog_progress, 100.0)

    def test_progress_is_zero_without_total(self):
        self.assertEqual(self.box.backlog_progress, 0.0,
                         "aucune division par zéro sur une boîte jamais importée")

    def test_restart_resets_the_counter(self):
        self.box.action_start_backlog()
        self._run(FakeImap())
        self.box.action_start_backlog()
        self.assertEqual(self.box.backlog_done_count, 0,
                         "sans remise à zéro, une relance ferait dépasser 100 %")

    def test_progress_never_exceeds_one_hundred(self):
        self.box.write({'backlog_total_count': 3, 'backlog_done_count': 9})
        self.assertEqual(self.box.backlog_progress, 100.0)

    def test_cron_rearms_while_running(self):
        cron = self.env.ref('oski_mail_inbox.ir_cron_backlog_import')
        fake = FakeImap()
        fake.uids = list(range(1, 250))  # plus d'une tranche
        self.box.action_start_backlog()
        # Échantillonné après action_start_backlog() : ce bouton arme lui
        # aussi le cron (test_start_backlog_triggers_cron_immediately),
        # sinon ce déclenchement-là suffirait à faire passer l'assertion
        # même si le réarmement de fin de tranche était supprimé.
        before = self.env['ir.cron.trigger'].search_count([('cron_id', '=', cron.id)])
        self._run(fake)
        self.assertEqual(self.box.backlog_state, 'running')
        after = self.env['ir.cron.trigger'].search_count([('cron_id', '=', cron.id)])
        self.assertGreater(after, before,
                           "une jauge adossée à un cron de 10 minutes regarde une barre immobile")

    def test_cron_does_not_rearm_once_done(self):
        cron = self.env.ref('oski_mail_inbox.ir_cron_backlog_import')
        self.box.action_start_backlog()
        self._run(FakeImap())
        self.assertEqual(self.box.backlog_state, 'done')
        before = self.env['ir.cron.trigger'].search_count([('cron_id', '=', cron.id)])
        self._run(FakeImap())
        self.assertEqual(
            self.env['ir.cron.trigger'].search_count([('cron_id', '=', cron.id)]), before)

    def test_start_backlog_triggers_cron_immediately(self):
        cron = self.env.ref('oski_mail_inbox.ir_cron_backlog_import')
        before = self.env['ir.cron.trigger'].search_count([('cron_id', '=', cron.id)])
        self.box.action_start_backlog()
        after = self.env['ir.cron.trigger'].search_count([('cron_id', '=', cron.id)])
        self.assertGreater(
            after, before,
            "sans ce réarmement, le formulaire resterait figé sur 'pending' jusqu'au "
            "prochain passage du cron (dix minutes) : le clic, le seul geste que "
            "cette fonctionnalité sert, verrait une barre immobile")

    def test_restart_resets_the_total(self):
        self.box.action_start_backlog()
        self._run(FakeImap())
        self.box.action_start_backlog()
        self.assertEqual(
            self.box.backlog_total_count, 0,
            "sans remise à zéro, le compteur lirait '0 / <total de la relance "
            "précédente>' avant que la première tranche n'ait tourné")

    def test_progress_full_on_empty_mailbox_done(self):
        fake = FakeImap()
        fake.uids = []
        self.box.action_start_backlog()
        self._run(fake)
        self.assertEqual(self.box.backlog_state, 'done')
        self.assertEqual(
            self.box.backlog_progress, 100.0,
            "un import terminé sur une boîte sans historique ne doit pas afficher "
            "0 % à côté du badge « Terminé »")

    def test_progress_reflects_a_shrunk_denominator_on_done(self):
        # backlog_since reculé en cours de route peut faire grossir le total
        # au-delà de ce que backlog_done_count a jamais compté (les UID déjà
        # hors de portée ne sont pas revisités). L'état 'done' seul ne doit
        # plus suffire à afficher 100 % : ce test aurait été vert sous
        # l'ancien raccourci inconditionnel, il ne l'est plus.
        self.box.write({
            'backlog_state': 'done',
            'backlog_total_count': 500,
            'backlog_done_count': 305,
        })
        self.assertEqual(self.box.backlog_progress, 61.0)

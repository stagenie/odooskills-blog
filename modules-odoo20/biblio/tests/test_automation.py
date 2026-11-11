from dateutil.relativedelta import relativedelta

from odoo import fields

from .common import BiblioCase


class TestAutomation(BiblioCase):
    """Les règles d'automatisation livrées par le module (data/library_automation.xml)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.today = fields.Date.context_today(cls.env['library.loan'])
        cls.copy_3 = cls.env['library.copy'].create({'book_id': cls.book.id})
        cls.todo = cls.env.ref('mail.mail_activity_data_todo')
        cls.call = cls.env.ref('mail.mail_activity_data_call')

    def _activities(self, loan, activity_type):
        return loan.activity_ids.filtered(lambda a: a.activity_type_id == activity_type)

    def test_long_loan_activity_on_create(self):
        # Créé par un agent d'accueil : la règle passe en sudo, l'activité lui revient.
        loan = self.env['library.loan'].with_user(self.user_desk).create({
            'member_id': self.member.id, 'copy_id': self.copy_1.id, 'duration': 30,
        })
        activity = self._activities(loan, self.todo)
        self.assertEqual(len(activity), 1)
        self.assertEqual(activity.summary, "Faire valider une durée de plus de 21 jours")
        self.assertEqual(activity.user_id, self.user_desk)
        self.assertEqual(activity.date_deadline, self.today + relativedelta(days=1))
        # 14 jours : pas d'activité.
        self.assertFalse(self._activities(self._emprunter(self.copy_2), self.todo))

    def test_long_loan_pre_domain_and_trigger_field(self):
        loan = self._emprunter(self.copy_1, duration=14)
        loan.duration = 28  # 14 -> 28 : le domaine avant (<= 21) et après (> 21) sont vrais
        self.assertEqual(len(self._activities(loan, self.todo)), 1)
        loan.duration = 35  # 28 -> 35 : déjà au-dessus de 21 avant, rien de plus
        self.assertEqual(len(self._activities(loan, self.todo)), 1)
        loan.reminder_count = 3  # champ non surveillé : la règle n'est pas évaluée
        self.assertEqual(len(self._activities(loan, self.todo)), 1)

    def test_returned_loan_queues_mail(self):
        loan = self._emprunter(self.copy_1)
        loan.action_return()
        mail = self.env['mail.mail'].search([('model', '=', 'library.loan'), ('res_id', '=', loan.id)])
        self.assertEqual(len(mail), 1)
        self.assertEqual(mail.state, 'outgoing')  # en file d'attente, pas envoyé
        self.assertEqual(mail.subject, "Retour enregistré : Python pour Odoo")
        self.assertEqual(mail.recipient_ids, self.member.partner_id)
        self.assertEqual(mail.mail_message_id.message_type, 'auto_comment')

    def test_lost_copy_leaves_shelf(self):
        shelf = self.env['library.shelf'].create({'name': "Réserve"})
        self.copy_3.shelf_id = shelf
        self.copy_3.state = 'lost'
        self.assertFalse(self.copy_3.shelf_id)

    def test_overdue_rule_runs_once_from_cron(self):
        rule = self.env.ref('biblio.automation_loan_overdue')
        cron = self.env.ref('base_automation.ir_cron_data_base_automation_check')
        self.assertTrue(cron.active)
        late = self._emprunter(self.copy_1, date_out=self.today - relativedelta(days=30))   # 16 j de retard
        recent = self._emprunter(self.copy_2, date_out=self.today - relativedelta(days=17))  # 3 j de retard
        returned = self._emprunter(self.copy_3, date_out=self.today - relativedelta(days=40))
        returned.action_return()
        with self.registry_test_mode():
            cron.method_direct_trigger()
        self.assertTrue(rule.last_run)
        self.assertEqual(len(self._activities(late, self.call)), 1)
        self.assertFalse(self._activities(recent, self.call))
        self.assertFalse(self._activities(returned, self.call))
        self.assertIn("Retard de 16 jours", late.message_ids[0].body)
        # Second passage : la fenêtre part de last_run, l'emprunt n'est pas repris.
        with self.registry_test_mode():
            cron.method_direct_trigger()
        self.assertEqual(len(self._activities(late, self.call)), 1)

    def test_cron_interval_follows_shortest_delay(self):
        cron = self.env.ref('base_automation.ir_cron_data_base_automation_check')
        rule = self.env.ref('biblio.automation_loan_overdue')
        self.assertEqual((cron.interval_number, cron.interval_type), (4, 'hours'))
        rule.write({'trg_date_range': 1, 'trg_date_range_type': 'hour'})
        self.assertEqual((cron.interval_number, cron.interval_type), (6, 'minutes'))
        # Le délai rallongé ne rallonge pas l'intervalle.
        rule.write({'trg_date_range': 7, 'trg_date_range_type': 'day'})
        self.assertEqual((cron.interval_number, cron.interval_type), (6, 'minutes'))

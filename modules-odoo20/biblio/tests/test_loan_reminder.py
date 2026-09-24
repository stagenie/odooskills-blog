from datetime import date

from odoo.addons.mail.tests.common import MailCase
from odoo.tests import freeze_time

from .common import BiblioCase


class TestLoanReminder(BiblioCase, MailCase):

    @freeze_time('2026-09-30')
    def test_cron_reminds_late_loans_once_a_day(self):
        late = self._emprunter(self.copy_1, date_out=date(2026, 9, 1))
        self._emprunter(self.copy_2)  # à l'heure : pas de relance
        with self.mock_mail_gateway():
            count = self.env['library.loan']._cron_relancer_retards()
        self.assertEqual(count, 1)
        self.assertEqual(late.reminder_count, 1)
        self.assertSentEmail(
            self.env.user.partner_id, [self.member.partner_id],
            subject="Retard : Python pour Odoo",
        )
        # Deuxième passage le même jour : rien.
        self.assertEqual(self.env['library.loan']._cron_relancer_retards(), 0)

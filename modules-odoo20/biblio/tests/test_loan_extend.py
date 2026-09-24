from odoo.exceptions import UserError
from odoo.tests import Form

from .common import BiblioCase


class TestLoanExtend(BiblioCase):

    def _assistant(self, loans):
        ctx = {'active_model': 'library.loan', 'active_ids': loans.ids}
        return Form(self.env['library.loan.extend'].with_user(self.user_desk).with_context(ctx))

    def test_extend_in_batch(self):
        loans = self._emprunter(self.copy_1) | self._emprunter(self.copy_2)
        echeances = loans.mapped('date_due')
        form = self._assistant(loans)
        form.days = 10
        form.save().action_extend()
        for loan, avant in zip(loans, echeances):
            self.assertEqual((loan.date_due - avant).days, 10)
            self.assertIn("Prolongé de <b>10</b> jour(s).", loan.message_ids[0].body)

    def test_returned_loan_refused(self):
        loan = self._emprunter(self.copy_1)
        loan.action_return()
        assistant = self._assistant(loan).save()
        with self.assertRaisesRegex(UserError, loan.reference):
            assistant.action_extend()

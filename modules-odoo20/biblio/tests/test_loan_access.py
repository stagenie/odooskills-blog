from odoo.exceptions import AccessError

from .common import BiblioCase


class TestLoanAccess(BiblioCase):

    def test_desk_can_lend_and_return(self):
        loan = self._emprunter(self.copy_1).with_user(self.user_desk)
        loan.action_return()
        self.assertEqual(loan.state, 'returned')

    def test_desk_cannot_create_book(self):
        with self.assertRaises(AccessError):
            self.env['library.book'].with_user(self.user_desk).create({'title': "Interdit"})

    def test_returned_loan_is_frozen(self):
        loan = self._emprunter(self.copy_1)
        loan.action_return()
        with self.assertRaises(AccessError):
            loan.with_user(self.user_manager).write({'duration': 30})

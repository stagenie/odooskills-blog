from datetime import date

from psycopg2.errors import ForeignKeyViolation

from odoo.exceptions import ValidationError
from odoo.tests import freeze_time
from odoo.tools import mute_logger

from .common import BiblioCase


class TestLoan(BiblioCase):

    def test_reference_sequence(self):
        loan = self._emprunter(self.copy_1, date_out=date(2026, 9, 1))
        self.assertRegex(loan.reference, r'^EMP/2026/\d{4}$')

    def test_copy_state_follows_loan(self):
        loan = self._emprunter(self.copy_1)
        self.assertEqual(self.copy_1.state, 'borrowed')
        loan.action_return()
        self.assertEqual(self.copy_1.state, 'available')
        self.assertEqual(loan.state, 'returned')

    def test_copy_cannot_be_borrowed_twice(self):
        self._emprunter(self.copy_1)
        with self.assertRaises(ValidationError):
            self._emprunter(self.copy_1)

    def test_borrowed_copy_cannot_be_deleted(self):
        self._emprunter(self.copy_1)
        with self.assertRaises(ForeignKeyViolation), mute_logger('odoo.sql_db'):
            self.copy_1.unlink()

    @freeze_time('2026-09-30')
    def test_is_late(self):
        loan = self._emprunter(self.copy_1, date_out=date(2026, 9, 1), duration=14)
        self.assertEqual(loan.date_due, date(2026, 9, 15))
        self.assertTrue(loan.is_late)
        self.assertEqual(loan.days_late, 15)
        self.assertIn(loan, self.env['library.loan'].search([('is_late', '=', True)]))

    def test_return_posts_note(self):
        loan = self._emprunter(self.copy_1)
        loan.action_return()
        note = loan.message_ids[0]
        self.assertEqual(note.subtype_id, self.env.ref('mail.mt_note'))
        self.assertIn(f"<b>{self.copy_1.name}</b>", note.body)

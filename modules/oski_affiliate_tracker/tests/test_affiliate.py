from datetime import date

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestAffiliate(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.comp_cur = cls.env.company.currency_id
        cls.other = cls.env['res.currency'].with_context(active_test=False).search(
            [('id', '!=', cls.comp_cur.id)], limit=1)
        cls.other.active = True
        # 1 devise société = 2 "autres" -> 100 autres = 50 société
        cls.env['res.currency.rate'].create({
            'name': '2026-07-01',
            'currency_id': cls.other.id,
            'rate': 2.0,
            'company_id': cls.env.company.id,
        })
        cls.program = cls.env['oski.affiliate.program'].create({
            'name': 'Test Program',
            'site': 'both',
            'currency_id': cls.comp_cur.id,
        })

    def _add(self, amount, status, d='2026-07-05', currency=None):
        return self.env['oski.affiliate.commission'].create({
            'program_id': self.program.id,
            'date': d,
            'amount': amount,
            'status': status,
            'currency_id': (currency or self.comp_cur).id,
        })

    def test_period_computed_from_date(self):
        c = self._add(10, 'paid', d='2026-03-09')
        self.assertEqual(c.period, '2026-03')

    def test_same_currency_no_conversion(self):
        c = self._add(120, 'confirmed')
        self.assertAlmostEqual(c.amount_company, 120.0, places=2)

    def test_foreign_currency_converted_to_company(self):
        c = self._add(100, 'paid', currency=self.other)
        # 100 "autres" / 2 = 50 en devise société
        self.assertAlmostEqual(c.amount_company, 50.0, places=2)

    def test_program_stats(self):
        self._add(100, 'paid')
        self._add(40, 'pending')
        self._add(60, 'confirmed')
        self.program.invalidate_recordset()
        self.assertEqual(self.program.commission_count, 3)
        self.assertAlmostEqual(self.program.total_earned, 200.0, places=2)
        self.assertAlmostEqual(self.program.total_pending, 40.0, places=2)
        self.assertAlmostEqual(self.program.total_paid, 100.0, places=2)

    def test_last_commission_date(self):
        self._add(10, 'paid', d='2026-01-01')
        self._add(10, 'paid', d='2026-08-15')
        self._add(10, 'paid', d='2026-05-05')
        self.program.invalidate_recordset()
        self.assertEqual(self.program.last_commission_date, date(2026, 8, 15))

    def test_action_view_commissions_domain(self):
        act = self.program.action_view_commissions()
        self.assertEqual(act['res_model'], 'oski.affiliate.commission')
        self.assertIn(('program_id', '=', self.program.id), act['domain'])
        self.assertEqual(act['context']['default_program_id'], self.program.id)

    def test_tag_unique_constraint(self):
        import psycopg2
        from odoo.tools import mute_logger
        self.env['oski.affiliate.tag'].create({'name': 'Dup'})
        with self.assertRaises(psycopg2.IntegrityError), mute_logger('odoo.sql_db'):
            with self.env.cr.savepoint():
                self.env['oski.affiliate.tag'].create({'name': 'Dup'})
                self.env.flush_all()

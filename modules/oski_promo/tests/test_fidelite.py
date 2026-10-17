from datetime import date

from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestOskiFidelite(TransactionCase):
    """Codes personnels à prix net garanti (loyalty.reward.oski_net_price)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.eur = cls.env.ref('base.EUR')
        cls.eur.active = True
        cls.pricelist = cls.env['product.pricelist'].create({
            'name': 'TEST EUR FIDELITE', 'currency_id': cls.eur.id})
        cls.pack = cls.env['product.template'].create({
            'name': 'TEST PACK 20', 'default_code': 'TESTF-PACK', 'type': 'service',
            'list_price': 59.0, 'taxes_id': [(5, 0, 0)], 'sale_ok': True,
        })
        cls.other = cls.env['product.template'].create({
            'name': 'TEST E1 20', 'default_code': 'TESTF-E1', 'type': 'service',
            'list_price': 29.0, 'taxes_id': [(5, 0, 0)], 'sale_ok': True,
        })
        cls.item = cls.env['product.pricelist.item'].create({
            'pricelist_id': cls.pricelist.id, 'applied_on': '1_product',
            'product_tmpl_id': cls.pack.id, 'compute_price': 'fixed', 'fixed_price': 59.0,
        })
        cls.program = cls.env['loyalty.program'].create({
            'name': 'TEST Fidélité palier A', 'program_type': 'coupons',
            'trigger': 'with_code', 'applies_on': 'current', 'currency_id': cls.eur.id,
            'pricelist_ids': [(6, 0, cls.pricelist.ids)],
            'date_to': date(2026, 12, 31),
            'rule_ids': [(5, 0, 0)],
            'communication_plan_ids': [(5, 0, 0)],
            'reward_ids': [(5, 0, 0), (0, 0, {
                'reward_type': 'discount', 'discount': 90.0, 'discount_mode': 'percent',
                'discount_applicability': 'specific',
                'discount_product_ids': [(6, 0, cls.pack.product_variant_id.ids)],
                'required_points': 1, 'oski_net_price': 5.90,
                'description': 'Pack à 5,90 €',
            })],
        })
        cls.reward = cls.program.reward_ids
        cls.alice = cls.env['res.partner'].create({'name': 'TEST Alice', 'email': 'alice@test.oski'})
        cls.bob = cls.env['res.partner'].create({'name': 'TEST Bob', 'email': 'bob@test.oski'})
        cls.card = cls.env['loyalty.card'].with_context(loyalty_no_mail=True).create({
            'program_id': cls.program.id, 'points': 1, 'code': 'TESTF-A-0001',
            'expiration_date': date(2026, 12, 31), 'oski_partner_id': cls.alice.id,
        })

    def _order(self, partner, product=None, date_order=None):
        vals = {
            'partner_id': partner.id, 'pricelist_id': self.pricelist.id,
            'order_line': [(0, 0, {'product_id': (product or self.pack).product_variant_id.id,
                                   'product_uom_qty': 1})],
        }
        if date_order:
            vals['date_order'] = date_order
        return self.env['sale.order'].create(vals)

    def _apply(self, order, code):
        res = order._try_apply_code(code)
        self.assertNotIn('error', res, res.get('error'))
        coupon, rewards = next(iter(res.items()))
        self.assertEqual(rewards, self.reward)
        order._apply_program_reward(rewards, coupon)
        return coupon

    def test_net_price_at_regular_price(self):
        order = self._order(self.alice)
        self.assertEqual(order.amount_total, 59.0)
        self._apply(order, 'TESTF-A-0001')
        self.assertAlmostEqual(order.amount_total, 5.90, places=2)

    def test_net_price_during_launch_price(self):
        # Prix de lancement : le pourcentage seul donnerait 4,40 € ; le prix net reste 5,90 €.
        self.item.fixed_price = 44.0
        order = self._order(self.alice)
        self.assertEqual(order.amount_total, 44.0)
        self._apply(order, 'TESTF-A-0001')
        self.assertAlmostEqual(order.amount_total, 5.90, places=2)
        # et la remise se recalcule si le panier change
        order._update_programs_and_rewards()
        self.assertAlmostEqual(order.amount_total, 5.90, places=2)

    def test_percent_only_when_no_net_price(self):
        self.reward.oski_net_price = 0
        self.item.fixed_price = 44.0
        order = self._order(self.alice)
        self._apply(order, 'TESTF-A-0001')
        self.assertAlmostEqual(order.amount_total, 4.40, places=2)

    def test_single_use(self):
        order = self._order(self.alice)
        self._apply(order, 'TESTF-A-0001')
        order.action_confirm()
        self.assertEqual(self.card.points, 0)
        again = self._order(self.alice)
        res = again._try_apply_code('TESTF-A-0001')
        self.assertIn('error', res)
        self.assertIn('already been used', res['error'])

    def test_code_not_locked_to_recipient(self):
        # Bob (autre partenaire, cas « invité ») peut consommer le code d'Alice.
        order = self._order(self.bob)
        self._apply(order, 'TESTF-A-0001')
        self.assertAlmostEqual(order.amount_total, 5.90, places=2)
        order._update_programs_and_rewards()
        self.assertAlmostEqual(order.amount_total, 5.90, places=2)

    def test_nothing_to_discount_on_other_product(self):
        order = self._order(self.alice, product=self.other)
        res = order._try_apply_code('TESTF-A-0001')
        coupon, rewards = next(iter(res.items()))
        with self.assertRaises(Exception):
            order._apply_program_reward(rewards, coupon)

    def test_expired_or_other_pricelist_refused(self):
        self.card.expiration_date = date(2026, 1, 1)
        res = self._order(self.alice)._try_apply_code('TESTF-A-0001')
        self.assertIn('expired', res.get('error', ''))
        self.card.expiration_date = date(2026, 12, 31)
        other_pl = self.env['product.pricelist'].create({'name': 'TEST AUTRE', 'currency_id': self.eur.id})
        order = self._order(self.alice)
        order.pricelist_id = other_pl
        res = order._try_apply_code('TESTF-A-0001')
        self.assertIn('error', res)

    def test_partner_computed_fields(self):
        self.assertEqual(self.alice.oski_coupon_code, 'TESTF-A-0001')
        self.assertEqual(self.alice.oski_coupon_label, 'Pack à 5,90 €')
        self.assertEqual(self.alice.oski_coupon_price_fmt, '5,90 €')
        self.assertEqual(self.alice.oski_coupon_expiration, date(2026, 12, 31))
        self.assertEqual(self.alice.oski_coupon_expiration_fmt, '31 décembre 2026')
        self.assertEqual(self.alice.oski_coupon_discount_fmt, '−90 %')
        self.assertFalse(self.bob.oski_coupon_code)
        self.assertFalse(self.bob.oski_coupon_discount_fmt)
        self.assertFalse(self.bob.oski_coupon_expiration_fmt)
        self.card.points = 0
        self.alice.invalidate_recordset()
        self.assertFalse(self.alice.oski_coupon_code)

    def test_net_price_constraint(self):
        with self.assertRaises(ValidationError):
            self.reward.discount_applicability = 'order'

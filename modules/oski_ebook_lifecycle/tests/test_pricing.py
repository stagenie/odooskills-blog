from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestOskiPricing(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.eb1 = cls.env.ref('oski_ebook_lifecycle.ebook_e1')
        cls.eb2 = cls.env.ref('oski_ebook_lifecycle.ebook_e2')
        P = cls.env['product.template']
        cls.mono1 = P.create({
            'name': 'TEST E1', 'default_code': 'TEST-E1',
            'ebook_ids': [(6, 0, cls.eb1.ids)],
            'oski_price_regular': 27.0, 'oski_price_launch': 24.0,
        })

    def test_offer_fields_exist_and_store(self):
        self.assertEqual(self.mono1.oski_price_regular, 27.0)
        self.assertEqual(self.mono1.oski_price_launch, 24.0)
        self.assertFalse(self.mono1.oski_launch_deadline)

    def _make_pricelist(self):
        pl = self.env['product.pricelist'].create({'name': 'TEST EUR'})
        ICP = self.env['ir.config_parameter'].sudo()
        ICP.set_param('oski.pricing.dzd_rate', '270')
        ICP.set_param('oski.pricing.eur_pricelist_id', str(pl.id))
        return pl

    def test_apply_sans_date(self):
        pl = self._make_pricelist()
        self.mono1._oski_apply_pricing_offer()
        self.assertEqual(self.mono1.list_price, 24.0 * 270)
        self.assertEqual(self.mono1.compare_list_price, 27.0 * 270)
        items = self.env['product.pricelist.item'].search([
            ('pricelist_id', '=', pl.id), ('product_tmpl_id', '=', self.mono1.id)])
        self.assertEqual(len(items), 1)
        self.assertFalse(items.date_end)
        self.assertEqual(items.fixed_price, 24.0)

    def test_apply_no_discount_clears_barre(self):
        self._make_pricelist()
        self.mono1.oski_price_launch = 27.0
        self.mono1._oski_apply_pricing_offer()
        self.assertEqual(self.mono1.compare_list_price, 0.0)

    def test_apply_avec_date_creates_two_items(self):
        pl = self._make_pricelist()
        self.mono1.oski_launch_deadline = '2099-12-31 22:59:59'
        self.mono1._oski_apply_pricing_offer()
        items = self.env['product.pricelist.item'].search([
            ('pricelist_id', '=', pl.id), ('product_tmpl_id', '=', self.mono1.id)])
        self.assertEqual(len(items), 2)
        dated = items.filtered(lambda i: i.date_end)
        self.assertEqual(dated.fixed_price, 24.0)
        self.assertEqual(items.filtered(lambda i: not i.date_end).fixed_price, 27.0)

    def test_incoherences_empty_after_apply(self):
        self._make_pricelist()
        self.mono1._oski_apply_pricing_offer()
        self.assertEqual(self.mono1.oski_pricing_incoherences(), [])

    def test_incoherences_detects_drift(self):
        self._make_pricelist()
        self.mono1._oski_apply_pricing_offer()
        self.mono1.compare_list_price = 999.0  # drift manuel
        issues = self.mono1.oski_pricing_incoherences()
        self.assertTrue(any('barré' in i for i in issues))

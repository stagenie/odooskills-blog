from freezegun import freeze_time

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestOskiPromoRender(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.eb1 = cls.env.ref('oski_ebook_lifecycle.ebook_e1')
        cls.pricelist = cls.env['product.pricelist'].create({'name': 'TEST EUR RENDER'})
        ICP = cls.env['ir.config_parameter'].sudo()
        ICP.set_param('oski.pricing.eur_pricelist_id', str(cls.pricelist.id))
        cls.mono = cls.env['product.template'].create({
            'name': 'TEST RENDER E1', 'default_code': 'TESTR-E1',
            'ebook_ids': [(6, 0, cls.eb1.ids)],
            'oski_price_regular': 27.0, 'oski_price_launch': 24.0,
        })
        cls.camp = cls.env['oski.promo.campaign'].create({
            'name': 'Été 2026', 'label_public': "Promotion d'été −30 %",
            'date_start': '2026-07-30 00:00:00',
            'date_end': '2026-08-02 22:00:00',
            'discount_percent': 30.0,
        })
        cls.camp.action_generate_lines()
        cls.camp.action_apply()
        cls.website = cls.env['website'].search([], limit=1)

    def _render(self, sku='TESTR-E1'):
        return self.env['ir.qweb']._render(
            'oski_promo.price_block',
            {'sku': sku, 'website': self.website})

    def test_helper_unknown_sku_is_safe(self):
        info = self.website.oski_price('NEXISTE-PAS')
        self.assertFalse(info['found'])
        self.assertEqual(info['payer'], 0.0)

    @freeze_time('2026-08-01 12:00:00')
    def test_bloc_pendant_promo(self):
        html = str(self._render())
        self.assertIn('16,80', html)
        self.assertIn('27', html)
        self.assertIn('data-deadline="2026-08-02T22:00:00Z"', html)
        self.assertIn('data-after="24"', html)
        self.assertIn('oski-countdown', html)

    @freeze_time('2026-08-03 12:00:00')
    def test_bloc_apres_promo(self):
        html = str(self._render())
        self.assertIn('24', html)
        self.assertNotIn('16,80', html)
        self.assertNotIn('data-deadline', html)
        self.assertNotIn('oski-countdown', html)

    @freeze_time('2026-08-03 12:00:00')
    def test_barre_persiste_hors_promo(self):
        """Le barré est permanent : c'est l'exigence initiale du client."""
        html = str(self._render())
        self.assertIn('oski-price-strike', html)
        self.assertIn('27', html)

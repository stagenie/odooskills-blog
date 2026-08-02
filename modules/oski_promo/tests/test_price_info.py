from freezegun import freeze_time

from odoo.tests import TransactionCase, tagged

from odoo.addons.oski_promo.models.product_template import oski_fmt


@tagged('post_install', '-at_install')
class TestOskiPriceInfo(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.eb1 = cls.env.ref('oski_ebook_lifecycle.ebook_e1')
        cls.pricelist = cls.env['product.pricelist'].create({'name': 'TEST EUR INFO'})
        ICP = cls.env['ir.config_parameter'].sudo()
        ICP.set_param('oski.pricing.dzd_rate', '270')
        ICP.set_param('oski.pricing.eur_pricelist_id', str(cls.pricelist.id))
        cls.mono = cls.env['product.template'].create({
            'name': 'TEST INFO E1', 'default_code': 'TESTI-E1',
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

    def test_fmt_entier_sans_decimale(self):
        self.assertEqual(oski_fmt(24.0), '24')

    def test_fmt_decimale_virgule_francaise(self):
        self.assertEqual(oski_fmt(16.80), '16,80')

    @freeze_time('2026-07-15 12:00:00')
    def test_avant_campagne(self):
        info = self.mono._oski_price_info()
        self.assertFalse(info['promo'])
        self.assertEqual(info['payer'], 24.0)
        self.assertEqual(info['barre'], 27.0)
        self.assertEqual(info['deadline_iso'], '')

    @freeze_time('2026-08-01 12:00:00')
    def test_pendant_campagne(self):
        info = self.mono._oski_price_info()
        self.assertTrue(info['promo'])
        self.assertEqual(info['payer'], 16.80)
        self.assertEqual(info['payer_fmt'], '16,80')
        self.assertEqual(info['barre'], 27.0)
        self.assertEqual(info['after'], 24.0)
        self.assertEqual(info['label'], "Promotion d'été −30 %")
        self.assertEqual(info['deadline_iso'], '2026-08-02T22:00:00Z')

    @freeze_time('2026-08-03 12:00:00')
    def test_apres_campagne(self):
        """Le cœur du module : après l'échéance, tout redevient normal
        sans qu'aucun code n'ait été exécuté pour cela."""
        info = self.mono._oski_price_info()
        self.assertFalse(info['promo'])
        self.assertEqual(info['payer'], 24.0)
        self.assertEqual(info['barre'], 27.0)
        self.assertEqual(info['deadline_iso'], '')
        self.assertEqual(self.camp.state, 'done')

    @freeze_time('2026-08-01 12:00:00')
    def test_campagne_desactivee_ignoree(self):
        self.camp.active = False
        info = self.mono._oski_price_info()
        self.assertFalse(info['promo'])

    @freeze_time('2026-08-01 12:00:00')
    def test_items_ecrases_eteignent_tout_le_mobilier_promo(self):
        """CRITICAL — `applied` peut mentir. Le script de tarification du
        module voisin oski_ebook_lifecycle purge le même espace d'items
        avec la même clé : après son passage, la campagne reste `applied`
        et « running » alors que le prix facturé est redevenu le plein
        tarif. Le mobilier promotionnel est piloté par le PRIX, jamais par
        le drapeau — sinon le site annonce une remise que la caisse
        n'accorde pas."""
        self.mono._oski_apply_pricing_offer()
        info = self.mono._oski_price_info()
        self.assertTrue(self.camp.applied)
        self.assertEqual(self.camp.state, 'running')
        self.assertEqual(info['payer'], 24.0)
        self.assertFalse(info['promo'])
        self.assertEqual(info['deadline_iso'], '')
        self.assertEqual(info['label'], '')

    @freeze_time('2026-08-01 12:00:00')
    def test_campagne_non_effective_ne_sort_pas_du_bandeau(self):
        """Même cause, autre surface : le bandeau de site est alimenté par
        website.oski_running_campaign(), qui doit lui aussi croire au prix."""
        website = self.env['website'].search([], limit=1)
        self.assertTrue(website.oski_running_campaign())
        self.mono._oski_apply_pricing_offer()
        self.assertFalse(website.oski_running_campaign())

from freezegun import freeze_time

from odoo.tests import TransactionCase, tagged

# Le garde-fou des tests et le détecteur de production doivent parler du
# MÊME filet. On IMPORTE donc le motif au lieu de le recopier : une copie
# diverge, et le quitus « liste vide » du détecteur devient mensonger sans
# qu'aucun test ne tombe.
from odoo.addons.oski_promo.models.website import OSKI_PRICE_RE


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

    @freeze_time('2026-08-01 12:00:00')
    def test_bloc_pendant_promo_expose_valeurs_numeriques(self):
        """data-barre / data-after-value : la version numérique brute que le
        JS de Task 8 doit comparer pour décider si le barré survit à
        l'échéance (barre <= after ⇒ le barré n'était que promotionnel)."""
        html = str(self._render())
        self.assertIn('data-barre="27.0"', html)
        self.assertIn('data-after-value="24.0"', html)

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

    def _render_banner(self):
        return str(self.env['ir.qweb']._render(
            'oski_promo.banner', {'website': self.website}))

    @freeze_time('2026-08-01 12:00:00')
    def test_bandeau_pendant_promo(self):
        html = self._render_banner()
        # t-out échappe l'apostrophe ASCII de label_public en entité HTML.
        self.assertIn("Promotion d&#39;été", html)
        self.assertIn('data-deadline="2026-08-02T22:00:00Z"', html)

    @freeze_time('2026-08-03 12:00:00')
    def test_bandeau_absent_apres_promo(self):
        html = self._render_banner()
        self.assertNotIn("Promotion d'été", html)
        self.assertNotIn('oski-promo-banner', html)

    def test_heritage_layout_present(self):
        vue = self.env.ref('oski_promo.banner_in_layout')
        self.assertEqual(vue.inherit_id, self.env.ref('website.layout'))

    @freeze_time('2026-08-01 12:00:00')
    def test_squelette_rend_les_prix_dynamiques(self):
        html = str(self.env['ir.qweb']._render(
            'oski_promo.landing_skeleton',
            {'sku': 'TESTR-E1', 'website': self.website}))
        self.assertIn('16,80', html)
        self.assertIn('data-oski-price="TESTR-E1"', html)

    def test_squelette_ne_contient_aucun_prix_en_dur(self):
        """Le squelette ne doit contenir aucun montant figé, sinon il
        recréerait la dette qu'il est censé supprimer."""
        arch = self.env.ref('oski_promo.landing_skeleton').arch
        self.assertIsNone(OSKI_PRICE_RE.search(arch))

    def test_squelette_documente_la_pose_du_sku(self):
        """La consigne « poser t-set sku en tête de page » ne doit pas
        vivre uniquement dans le README : celui qui duplique le template
        lit le template."""
        arch = self.env.ref('oski_promo.landing_skeleton').arch
        self.assertIn('t-set="sku"', arch)

    def test_garde_fou_prix_en_dur_detecte_montant_en_lettres(self):
        """Preuve que le garde-fou ci-dessus est réellement contraignant :
        un montant écrit en toutes lettres (sans le symbole €) doit être
        détecté, sinon la garantie est illusoire."""
        self.assertIsNotNone(
            OSKI_PRICE_RE.search("la formation à 24 euros"))

    def test_dict_neutre_a_les_memes_cles_que_le_resolveur(self):
        """Le dict de repli d'oski_price() est recopié à la main depuis
        _oski_price_info(). Toute divergence donnerait une KeyError au
        rendu d'une page dont le sku a été mal saisi — c'est-à-dire
        exactement le cas que le repli est censé amortir."""
        neutre = self.website.oski_price('NEXISTE-PAS')
        reel = self.website.oski_price('TESTR-E1')
        self.assertEqual(set(neutre), set(reel))

    @freeze_time('2026-08-01 12:00:00')
    def test_bloc_et_bandeau_muets_si_items_ecrases(self):
        """CRITICAL — le module lifecycle écrit le même espace d'items avec
        la même purge. Rejouer sa tarification pendant une campagne efface
        les items promotionnels sans rien écrire côté campagne : `applied`
        reste vrai, `state` reste « running », mais la caisse encaisse de
        nouveau le plein tarif. Ni bandeau, ni libellé, ni compteur, ni
        barré promotionnel ne doivent survivre à ça."""
        self.mono._oski_apply_pricing_offer()
        self.assertTrue(self.camp.applied)
        self.assertEqual(self.camp.state, 'running')

        html = str(self._render())
        self.assertNotIn('16,80', html)
        self.assertNotIn('data-deadline', html)
        self.assertNotIn('oski-countdown', html)

        bandeau = self._render_banner()
        self.assertNotIn('oski-promo-banner', bandeau)
        self.assertNotIn("Promotion d&#39;été", bandeau)

from psycopg2 import IntegrityError

from odoo import fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests import TransactionCase, tagged
from odoo.tools import mute_logger


@tagged('post_install', '-at_install')
class TestOskiPromoCampaign(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.eb1 = cls.env.ref('oski_ebook_lifecycle.ebook_e1')
        cls.pricelist = cls.env['product.pricelist'].create({'name': 'TEST EUR PROMO'})
        ICP = cls.env['ir.config_parameter'].sudo()
        ICP.set_param('oski.pricing.dzd_rate', '270')
        ICP.set_param('oski.pricing.eur_pricelist_id', str(cls.pricelist.id))
        cls.mono = cls.env['product.template'].create({
            'name': 'TEST PROMO E1', 'default_code': 'TESTP-E1',
            'ebook_ids': [(6, 0, cls.eb1.ids)],
            'oski_price_regular': 27.0, 'oski_price_launch': 24.0,
        })

    def _campaign(self, **kw):
        vals = {
            'name': 'Été 2026', 'label_public': "Promotion d'été −30 %",
            'date_start': '2026-07-30 00:00:00',
            'date_end': '2026-08-02 22:00:00',
            'discount_percent': 30.0,
        }
        vals.update(kw)
        return self.env['oski.promo.campaign'].create(vals)

    def test_campaign_created_is_draft(self):
        camp = self._campaign()
        self.assertFalse(camp.applied)
        self.assertEqual(camp.state, 'draft')

    def test_end_before_start_refused(self):
        with self.assertRaises(ValidationError):
            self._campaign(date_start='2026-08-05 00:00:00',
                           date_end='2026-08-01 00:00:00')

    def test_deadline_iso_format(self):
        camp = self._campaign()
        self.assertEqual(camp.oski_deadline_iso(), '2026-08-02T22:00:00Z')

    def test_line_product_unique_per_campaign(self):
        camp = self._campaign()
        Line = self.env['oski.promo.line']
        Line.create({'campaign_id': camp.id, 'product_tmpl_id': self.mono.id,
                     'price_promo': 16.80})
        with self.assertRaises(IntegrityError), mute_logger('odoo.sql_db'):
            Line.create({'campaign_id': camp.id, 'product_tmpl_id': self.mono.id,
                         'price_promo': 15.00})
            self.env.flush_all()

    def test_line_related_prices(self):
        camp = self._campaign()
        line = self.env['oski.promo.line'].create({
            'campaign_id': camp.id, 'product_tmpl_id': self.mono.id,
            'price_promo': 16.80})
        self.assertEqual(line.price_current, 24.0)
        self.assertEqual(line.price_regular, 27.0)

    def test_generate_lines_covers_all_priced_products(self):
        camp = self._campaign()
        camp.action_generate_lines()
        produits = self.env['product.template'].search([('ebook_ids', '!=', False)])
        self.assertEqual(len(camp.line_ids), len(produits))
        self.assertIn(self.mono, camp.line_ids.product_tmpl_id)

    def test_generate_lines_applies_percent(self):
        camp = self._campaign()
        camp.action_generate_lines()
        ligne = camp.line_ids.filtered(lambda l: l.product_tmpl_id == self.mono)
        self.assertEqual(ligne.price_promo, 16.80)  # 24 − 30 %

    def test_generate_lines_is_idempotent(self):
        camp = self._campaign()
        camp.action_generate_lines()
        premier = len(camp.line_ids)
        camp.action_generate_lines()
        self.assertEqual(len(camp.line_ids), premier)

    def test_generate_lines_picks_up_new_product(self):
        """Un ebook ajouté plus tard entre dans la campagne sans code."""
        camp = self._campaign()
        camp.action_generate_lines()
        avant = len(camp.line_ids)
        eb3 = self.env.ref('oski_ebook_lifecycle.ebook_e3')
        self.env['product.template'].create({
            'name': 'TEST PROMO E4', 'default_code': 'TESTP-E4',
            'ebook_ids': [(6, 0, eb3.ids)],
            'oski_price_regular': 30.0, 'oski_price_launch': 26.0,
        })
        camp.action_generate_lines()
        self.assertEqual(len(camp.line_ids), avant + 1)

    def test_generate_lines_refused_when_applied(self):
        camp = self._campaign()
        camp.action_generate_lines()
        camp.applied = True
        with self.assertRaises(UserError):
            camp.action_generate_lines()

    def _items(self, produit=None):
        return self.env['product.pricelist.item'].search([
            ('pricelist_id', '=', self.pricelist.id),
            ('product_tmpl_id', '=', (produit or self.mono).id)])

    def _prix_a(self, date):
        return self.pricelist._get_product_price(
            self.mono.product_variant_id, 1.0, date=date)

    def test_apply_creates_three_items(self):
        camp = self._campaign()
        camp.action_generate_lines()
        camp.action_apply()
        self.assertEqual(len(self._items()), 3)
        self.assertTrue(camp.applied)

    def test_apply_price_before_during_after(self):
        camp = self._campaign()
        camp.action_generate_lines()
        camp.action_apply()
        self.assertEqual(self._prix_a('2026-07-01 12:00:00'), 24.0)
        self.assertEqual(self._prix_a('2026-08-01 12:00:00'), 16.80)
        self.assertEqual(self._prix_a('2026-08-03 12:00:00'), 24.0)

    def test_apply_never_two_active_items(self):
        """Aucune date ne doit voir deux items actifs : le prix serait ambigu."""
        camp = self._campaign()
        camp.action_generate_lines()
        camp.action_apply()
        dates = ['2026-07-01 00:00:00', '2026-07-29 23:59:59',
                 '2026-07-30 00:00:00', '2026-08-01 00:00:00',
                 '2026-08-02 22:00:00', '2026-08-02 22:00:01',
                 '2026-09-01 00:00:00']
        for date in dates:
            actifs = self._items().filtered(
                lambda i: (not i.date_start or fields.Datetime.to_string(i.date_start) <= date)
                and (not i.date_end or fields.Datetime.to_string(i.date_end) >= date))
            self.assertEqual(len(actifs), 1, "prix ambigu au %s" % date)

    def test_apply_is_idempotent(self):
        """Deux applications successives laissent trois items, pas six."""
        camp = self._campaign()
        camp.action_generate_lines()
        camp.action_apply()
        camp.action_apply()
        self.assertEqual(len(self._items()), 3)

    def test_apply_refuses_overlapping_campaign(self):
        camp = self._campaign()
        camp.action_generate_lines()
        camp.action_apply()
        autre = self._campaign(name='Chevauchante',
                               date_start='2026-08-01 00:00:00',
                               date_end='2026-08-10 00:00:00')
        autre.action_generate_lines()
        with self.assertRaises(UserError):
            autre.action_apply()

    def test_apply_refuses_without_lines(self):
        camp = self._campaign()
        with self.assertRaises(UserError):
            camp.action_apply()

    def test_apply_spares_orphan_item(self):
        """Un item sans produit (il en existe un en prod) doit survivre."""
        orphelin = self.env['product.pricelist.item'].create({
            'pricelist_id': self.pricelist.id,
            'applied_on': '3_global', 'compute_price': 'fixed', 'fixed_price': 5.0})
        camp = self._campaign()
        camp.action_generate_lines()
        camp.action_apply()
        self.assertTrue(orphelin.exists())

    def test_apply_price_at_exact_boundaries(self):
        """Interroge le moteur réel _get_product_price aux quatre secondes
        de bascule, là où une erreur de borne se manifesterait."""
        camp = self._campaign()
        camp.action_generate_lines()
        camp.action_apply()
        self.assertEqual(self._prix_a('2026-07-29 23:59:59'), 24.0)
        self.assertEqual(self._prix_a('2026-07-30 00:00:00'), 16.80)
        self.assertEqual(self._prix_a('2026-08-02 22:00:00'), 16.80)
        self.assertEqual(self._prix_a('2026-08-02 22:00:01'), 24.0)

    def test_apply_refuses_unfinished_campaign_without_overlap(self):
        """Deux campagnes sans aucun chevauchement de période, sur le même
        produit : la seconde application purgerait quand même les items
        encore actifs de la première, donc doit être refusée."""
        camp = self._campaign(name='Septembre',
                               date_start='2026-09-01 00:00:00',
                               date_end='2026-09-10 00:00:00')
        camp.action_generate_lines()
        camp.action_apply()
        autre = self._campaign(name='Octobre',
                               date_start='2026-10-01 00:00:00',
                               date_end='2026-10-10 00:00:00')
        autre.action_generate_lines()
        with self.assertRaises(UserError):
            autre.action_apply()

    def _produit(self, name, code, **prix):
        eb3 = self.env.ref('oski_ebook_lifecycle.ebook_e3')
        vals = {'name': name, 'default_code': code,
                'ebook_ids': [(6, 0, eb3.ids)]}
        vals.update(prix)
        return self.env['product.template'].create(vals)

    def test_apply_refuses_product_without_price(self):
        """CRITICAL — un produit créé avant la saisie de ses prix entre dans
        la campagne par la découverte automatique. L'item de repli n'ayant
        PAS de date de fin, un prix nul y survivrait à la campagne et le
        produit resterait gratuit pour toujours."""
        sans_prix = self._produit('TEST PROMO SANS PRIX', 'TESTP-NOPRICE')
        camp = self._campaign()
        camp.action_generate_lines()
        self.assertIn(sans_prix, camp.line_ids.product_tmpl_id)
        with self.assertRaises(UserError) as ctx:
            camp.action_apply()
        self.assertIn('TEST PROMO SANS PRIX', str(ctx.exception))
        # Le contrôle tourne AVANT toute écriture : aucun item, nulle part.
        self.assertFalse(self._items())
        self.assertFalse(self._items(sans_prix))
        self.assertFalse(camp.applied)

    def test_apply_refuses_discount_over_100(self):
        """Une remise supérieure à 100 % donne un prix négatif."""
        camp = self._campaign(discount_percent=130.0)
        camp.action_generate_lines()
        with self.assertRaises(UserError) as ctx:
            camp.action_apply()
        self.assertIn('TEST PROMO E1', str(ctx.exception))
        self.assertFalse(self._items())

    def test_apply_refuses_promo_above_current(self):
        """Saisie de 168 au lieu de 16,80 : une « promotion » qui augmente
        le prix n'en est pas une."""
        camp = self._campaign()
        camp.action_generate_lines()
        camp.line_ids.filtered(
            lambda l: l.product_tmpl_id == self.mono).price_promo = 168.0
        with self.assertRaises(UserError) as ctx:
            camp.action_apply()
        self.assertIn('TEST PROMO E1', str(ctx.exception))
        self.assertFalse(self._items())

    def test_two_applied_campaigns_on_disjoint_products(self):
        """Deux campagnes appliquées en même temps sur des produits
        DISJOINTS sont légitimes : aucun item ne se marche dessus. Sans ce
        test, retirer l'intersection produit de _check_no_overlap rendrait
        toute seconde campagne impossible et rien ne tomberait."""
        autre_produit = self._produit(
            'TEST PROMO E3 DISJOINT', 'TESTP-E3D',
            oski_price_regular=25.0, oski_price_launch=22.0)
        camp1 = self._campaign(name='Sur E1')
        camp1.line_ids = [(0, 0, {'product_tmpl_id': self.mono.id,
                                  'price_promo': 16.80})]
        camp1.action_apply()
        camp2 = self._campaign(name='Sur E3')
        camp2.line_ids = [(0, 0, {'product_tmpl_id': autre_produit.id,
                                  'price_promo': 15.40})]
        camp2.action_apply()
        self.assertTrue(camp1.applied)
        self.assertTrue(camp2.applied)
        self.assertEqual(len(self._items()), 3)
        self.assertEqual(len(self._items(autre_produit)), 3)

    def test_line_price_current_falls_back_to_regular(self):
        """Sans prix de lancement — cas normal d'un ebook sans remise
        permanente — la colonne « Prix courant » de la grille affichait
        0,00 € alors que l'item de repli sera créé au prix régulier.
        L'opérateur arbitrait un prix promo en regardant un zéro."""
        sans_lancement = self._produit(
            'TEST PROMO SANS LANCEMENT', 'TESTP-NOLAUNCH',
            oski_price_regular=30.0)
        camp = self._campaign()
        ligne = self.env['oski.promo.line'].create({
            'campaign_id': camp.id, 'product_tmpl_id': sans_lancement.id,
            'price_promo': 21.0})
        self.assertEqual(ligne.price_current, 30.0)

    def test_write_dates_refused_when_applied(self):
        camp = self._campaign()
        camp.action_generate_lines()
        camp.action_apply()
        with self.assertRaises(UserError):
            camp.date_end = '2026-08-15 00:00:00'

    def test_cancel_restores_single_item(self):
        camp = self._campaign()
        camp.action_generate_lines()
        camp.action_apply()
        camp.action_cancel()
        items = self._items()
        self.assertEqual(len(items), 1)
        self.assertEqual(items.fixed_price, 24.0)
        self.assertFalse(items.date_start)
        self.assertFalse(items.date_end)
        self.assertFalse(camp.applied)

    def test_cancel_then_reapply(self):
        camp = self._campaign()
        camp.action_generate_lines()
        camp.action_apply()
        camp.action_cancel()
        camp.action_apply()
        self.assertEqual(len(self._items()), 3)

    def test_cancel_spares_orphan_item(self):
        orphelin = self.env['product.pricelist.item'].create({
            'pricelist_id': self.pricelist.id,
            'applied_on': '3_global', 'compute_price': 'fixed', 'fixed_price': 5.0})
        camp = self._campaign()
        camp.action_generate_lines()
        camp.action_apply()
        camp.action_cancel()
        self.assertTrue(orphelin.exists())

    def test_action_view_mode_uses_list(self):
        """« tree » n'existe plus en v19 : l'action planterait au chargement."""
        action = self.env.ref('oski_promo.action_campaign')
        self.assertEqual(action.view_mode, 'list,form')

    def test_form_view_loads(self):
        camp = self._campaign()
        vue = self.env.ref('oski_promo.view_campaign_form')
        arch = camp.get_view(vue.id, 'form')['arch']
        self.assertIn('label_public', arch)

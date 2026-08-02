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

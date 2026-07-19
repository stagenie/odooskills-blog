from odoo.tests import HttpCase, tagged


@tagged('post_install', '-at_install')
class TestWording(HttpCase):
    def test_homepage_no_longer_shows_popup_percent(self):
        """Popup retiré le 19/07/2026 (cf. test_popup_render.py) : la mention
        du pourcentage de bienvenue portée par le popup ne doit plus
        apparaître sur la page d'accueil. Le CTA produit (test suivant)
        continue lui de l'afficher, indépendamment du popup."""
        self.env['ir.config_parameter'].sudo().set_param(
            'oski_lead_magnet.welcome_percent', '30')
        html = self.url_open('/').text
        self.assertNotIn('-30%', html)

    def test_product_page_shows_cta(self):
        tmpl = self.env['product.template'].create({
            'name': 'E-cta', 'is_published': True, 'list_price': 27,
        })
        ebook = self.env['oski.ebook'].create({
            'code': 'ECTA', 'name': 'E-cta',
            'partner_category_id': self.env['res.partner.category'].create(
                {'name': 'Client E-cta'}).id,
        })
        tmpl.write({'ebook_ids': [(6, 0, ebook.ids)], 'oski_price_regular': 27.0,
                    'oski_price_launch': 27.0})
        self.env['ir.config_parameter'].sudo().set_param(
            'oski_lead_magnet.welcome_percent', '30')
        html = self.url_open('/shop/%s' % tmpl.id).text
        self.assertIn('osk-open-popup', html)
        self.assertIn('-30%', html)

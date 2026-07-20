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

    def test_product_cta_absent_on_shop_card_and_product_page(self):
        """CTA remise inscrit retiré le 19/07/2026 (product_cta_templates.xml
        supprimé) : la remise est désormais permanente sur le prix affiché et
        communiquée par email aux abonnés, plus par ce lien/badge qui
        n'ouvrait plus rien depuis le retrait du popup (cf.
        test_popup_render.py). Ni le badge de la carte catalogue ni le lien
        de la fiche produit ne doivent plus être rendus."""
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
        product_html = self.url_open('/shop/%s' % tmpl.id).text
        self.assertNotIn('osk-open-popup', product_html)
        self.assertNotIn('-30%', product_html)
        shop_html = self.url_open('/shop').text
        self.assertNotIn('osk-open-popup', shop_html)
        self.assertNotIn('si inscrit', shop_html)

from odoo import api, fields, models


class Website(models.Model):
    _inherit = 'website'

    @api.model
    def oski_price(self, sku):
        """Point d'entrée unique des templates. Tolérant : une référence
        inconnue rend un dict neutre plutôt qu'une page en erreur."""
        produit = self.env['product.template'].sudo().search(
            [('default_code', '=', sku)], limit=1)
        if not produit:
            return {'barre': 0.0, 'payer': 0.0, 'after': 0.0,
                    'barre_fmt': '', 'payer_fmt': '', 'after_fmt': '',
                    'promo': False, 'deadline_iso': '', 'label': '',
                    'found': False}
        info = produit._oski_price_info()
        info['found'] = True
        return info

    @api.model
    def oski_running_campaign(self):
        """Campagne en cours, tous produits confondus : alimente le bandeau."""
        now = fields.Datetime.now()
        return self.env['oski.promo.campaign'].sudo().search([
            ('applied', '=', True), ('active', '=', True),
            ('date_start', '<=', now), ('date_end', '>=', now),
        ], limit=1)

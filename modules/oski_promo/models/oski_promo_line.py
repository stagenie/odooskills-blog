from odoo import api, fields, models


class OskiPromoLine(models.Model):
    _name = 'oski.promo.line'
    _description = 'Ligne de campagne promotionnelle OdooSkills'
    _order = 'campaign_id, id'

    campaign_id = fields.Many2one(
        'oski.promo.campaign', string='Campagne',
        required=True, ondelete='cascade', index=True)
    product_tmpl_id = fields.Many2one(
        'product.template', string='Produit', required=True,
        domain=[('ebook_ids', '!=', False)],
        help="Produit tarifé (mono-ebook ou pack).")
    price_promo = fields.Float(
        string='Prix promo (€)', digits='Product Price', required=True,
        help="Prix EUR appliqué pendant la campagne.")
    price_current = fields.Float(
        string='Prix courant (€)', compute='_compute_price_current',
        digits='Product Price',
        help="Prix hors promotion. C'est lui qui reprend la main à l'échéance.")
    price_regular = fields.Float(
        related='product_tmpl_id.oski_price_regular',
        string='Barré (€)', readonly=True)

    @api.depends('product_tmpl_id.oski_price_launch',
                 'product_tmpl_id.oski_price_regular')
    def _compute_price_current(self):
        """« launch or regular », comme partout ailleurs dans le module.

        Un simple related sur oski_price_launch affichait 0,00 € pour un
        ebook sans remise permanente — cas normal — alors que la ligne
        avait bien été pré-remplie depuis le prix régulier et que l'item
        de repli sera créé à ce prix régulier. L'opérateur arbitrait un
        prix promotionnel en regardant un zéro.
        """
        for line in self:
            produit = line.product_tmpl_id
            line.price_current = (
                produit.oski_price_launch or produit.oski_price_regular)

    _unique_product_per_campaign = models.Constraint(
        'unique(campaign_id, product_tmpl_id)',
        "Un produit ne peut figurer qu'une seule fois dans une campagne.")

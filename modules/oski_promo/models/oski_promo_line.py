from odoo import fields, models


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
        related='product_tmpl_id.oski_price_launch',
        string='Prix courant (€)', readonly=True,
        help="Prix hors promotion. C'est lui qui reprend la main à l'échéance.")
    price_regular = fields.Float(
        related='product_tmpl_id.oski_price_regular',
        string='Barré (€)', readonly=True)

    _unique_product_per_campaign = models.Constraint(
        'unique(campaign_id, product_tmpl_id)',
        "Un produit ne peut figurer qu'une seule fois dans une campagne.")

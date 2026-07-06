from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    ebook_ids = fields.Many2many(
        'oski.ebook', 'oski_ebook_product_rel', 'product_tmpl_id', 'ebook_id',
        string='Ebooks inclus',
        help="Ebooks accordés à l'achat de ce produit (mono ou pack).")
    lifecycle_tier_category_id = fields.Many2one(
        'res.partner.category', string='Tier client',
        help="Tag tier posé à l'achat (ex. Client Pack, Client Trilogie). Vide sur un mono-ebook.")
    oski_price_regular = fields.Float(
        string='Prix régulier (€)', digits='Product Price',
        help="Prix de référence EUR affiché barré. Source de vérité du barré.")
    oski_price_launch = fields.Float(
        string='Prix remisé (€)', digits='Product Price',
        help="Prix EUR effectivement payé. Égal au régulier si pas de remise.")
    oski_launch_deadline = fields.Datetime(
        string='Fin de la remise',
        help="Vide = remise sans date (barré permanent, pas de compte à rebours). "
             "Rempli = lancement daté avec compte à rebours + retour auto au régulier.")
    oski_pack_bonus = fields.Float(
        string='Bonus pack (€)', digits='Product Price',
        help="Remise bundle retranchée à la somme des membres (assistant prix pack).")

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

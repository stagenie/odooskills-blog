from odoo import fields, models


class AffiliateTag(models.Model):
    _name = 'oski.affiliate.tag'
    _description = "Catégorie de programme d'affiliation"
    _order = 'name'

    name = fields.Char(required=True)
    color = fields.Integer(string='Couleur')

    _unique_name = models.Constraint('UNIQUE(name)', "Cette catégorie existe déjà.")

from odoo import fields, models


class AffiliateLink(models.Model):
    _name = 'oski.affiliate.link'
    _description = "Lien d'affiliation"
    _order = 'sequence, id'

    program_id = fields.Many2one(
        'oski.affiliate.program', string='Programme',
        required=True, ondelete='cascade', index=True)
    sequence = fields.Integer(default=10)
    name = fields.Char(
        string='Libellé', required=True,
        help="À quoi sert ce lien (ex. « Article blog X », « Bannière sidebar », « Newsletter »).")
    url = fields.Char(string='Lien', required=True)
    campaign = fields.Char(string='Campagne / emplacement')
    note = fields.Char(string='Note')
    active = fields.Boolean(default=True)

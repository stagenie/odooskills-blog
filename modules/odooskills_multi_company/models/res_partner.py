from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    odooskills_hourly_rate = fields.Float(
        string="Taux horaire d'intervention",
        company_dependent=True,
    )

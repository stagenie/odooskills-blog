from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    oski_parc_prefixe = fields.Char('Préfixe du matériel', default='MAT')

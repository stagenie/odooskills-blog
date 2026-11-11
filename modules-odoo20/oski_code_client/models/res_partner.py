from odoo import models


class ResPartner(models.Model):
    _name = 'res.partner'
    _inherit = ['res.partner', 'oski.code.mixin']
    _oski_code_prefixe = 'CLI'

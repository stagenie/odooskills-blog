from odoo import fields, models


class TestOskiDocument(models.Model):
    _name = 'test.oski.document'
    _inherit = ['oski.code.mixin']
    _description = 'Document de test du mixin de code'
    _oski_code_prefixe = 'DOC'

    name = fields.Char(required=True)

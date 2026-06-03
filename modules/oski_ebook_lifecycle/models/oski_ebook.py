from odoo import fields, models


class OskiEbook(models.Model):
    _name = 'oski.ebook'
    _description = "OdooSkills Ebook"

    name = fields.Char(required=True)

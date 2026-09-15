from odoo import fields, models


class WorkSite(models.Model):
    _name = 'odooskills.work.site'
    _description = "Site d'intervention"

    name = fields.Char(string="Nom", required=True)
    # Vide = site partagé entre toutes les sociétés
    company_id = fields.Many2one('res.company', string="Société", index=True)

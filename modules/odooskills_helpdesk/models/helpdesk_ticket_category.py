from odoo import models, fields


class HelpdeskTicketCategory(models.Model):
    """Catégorie de ticket — modèle persistant simple."""
    _name = 'helpdesk.ticket.category'
    _description = 'Catégorie de ticket helpdesk'

    name = fields.Char(string='Nom', required=True)
    color = fields.Integer(string='Couleur')

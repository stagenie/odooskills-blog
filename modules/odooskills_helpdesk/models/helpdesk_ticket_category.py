from odoo import models, fields


class HelpdeskTicketCategory(models.Model):
    """Catégorie de ticket — modèle persistant simple."""
    _name = 'helpdesk.ticket.category'
    _description = 'Catégorie de ticket helpdesk'
    _order = 'sequence, name'
    _rec_name = 'name'

    _unique_name = models.Constraint(
        'UNIQUE (name)',
        "Le nom de la catégorie doit être unique.",
    )

    name = fields.Char(string='Nom', required=True)
    sequence = fields.Integer(string='Séquence', default=10)
    color = fields.Integer(string='Couleur')

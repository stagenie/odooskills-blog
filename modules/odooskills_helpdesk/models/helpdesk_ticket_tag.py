from odoo import models, fields


class HelpdeskTicketTag(models.Model):
    """Tag — modèle cible de la relation Many2many avec le ticket.

    Un tag peut être associé à plusieurs tickets ;
    un ticket peut avoir plusieurs tags.
    """
    _name = 'helpdesk.ticket.tag'
    _description = 'Tag de ticket helpdesk'
    _order = 'name'

    name = fields.Char(string='Nom', required=True)
    color = fields.Integer(string='Couleur', default=0)

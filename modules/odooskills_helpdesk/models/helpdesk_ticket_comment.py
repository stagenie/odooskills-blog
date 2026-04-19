from odoo import models, fields


class HelpdeskTicketComment(models.Model):
    """Commentaire interne lié à un ticket — modèle "many" de la relation One2many.

    La clé étrangère (FK) se déclare ICI, sur le modèle enfant.
    Le ticket expose la relation inverse via One2many + inverse_name.
    """
    _name = 'helpdesk.ticket.comment'
    _description = 'Commentaire ticket helpdesk'
    _order = 'create_date desc'

    # Many2one vers le ticket : la FK réelle en base (helpdesk_ticket_id)
    ticket_id = fields.Many2one(
        comodel_name='helpdesk.ticket',
        string='Ticket',
        required=True,
        ondelete='cascade',   # suppression du ticket → supprime ses commentaires
        index=True,
    )
    body = fields.Text(string='Commentaire', required=True)
    author_id = fields.Many2one(
        comodel_name='res.users',
        string='Auteur',
        default=lambda self: self.env.user,
        ondelete='set null',
    )

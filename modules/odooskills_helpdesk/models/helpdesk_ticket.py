from odoo import models, fields


class HelpdeskTicket(models.Model):
    """Ticket de support — modèle persistant.

    Hérite de models.Model : données stockées en base PostgreSQL,
    durée de vie illimitée, visible dans les vues backend.
    """
    _name = 'helpdesk.ticket'
    _description = 'Ticket Helpdesk'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'odooskills.helpdesk.mixin']

    name = fields.Char(string='Sujet', required=True, tracking=True)
    description = fields.Text(string='Description')
    category_id = fields.Many2one(
        comodel_name='helpdesk.ticket.category',
        string='Catégorie',
        ondelete='restrict',
    )
    partner_id = fields.Many2one('res.partner', string='Client')
    state = fields.Selection(
        selection=[
            ('new', 'Nouveau'),
            ('in_progress', 'En cours'),
            ('done', 'Résolu'),
        ],
        default='new',
        required=True,
        tracking=True,
    )

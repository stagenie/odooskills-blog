from odoo import models, fields


class HelpdeskTicket(models.Model):
    """Ticket de support — modèle persistant.

    Hérite de models.Model : données stockées en base PostgreSQL,
    durée de vie illimitée, visible dans les vues backend.
    """
    _name = 'helpdesk.ticket'
    _description = 'Ticket Helpdesk'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'odooskills.helpdesk.mixin']
    _order = 'priority desc, create_date desc'
    _rec_name = 'name'

    # Contrainte d'unicité en Odoo 19 — remplace _sql_constraints
    _unique_reference = models.Constraint(
        'UNIQUE (reference)',
        "La référence du ticket doit être unique.",
    )

    name = fields.Char(string='Sujet', required=True, tracking=True)
    reference = fields.Char(string='Référence', copy=False, index=True)
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

from odoo import api, models, fields


class ResPartner(models.Model):
    """Extension de res.partner — héritage classique par _inherit.

    Pas de _name : on étend le modèle existant. La table reste
    `res_partner`, on y ajoute simplement de nouvelles colonnes
    et on expose un compteur de tickets côté fiche partenaire.
    """
    _inherit = 'res.partner'

    is_vip = fields.Boolean(
        string='Client VIP',
        default=False,
        help="Clients prioritaires — SLA réduit, assignation dédiée.",
    )
    ticket_ids = fields.One2many(
        comodel_name='helpdesk.ticket',
        inverse_name='partner_id',
        string='Tickets',
    )
    ticket_count = fields.Integer(
        string='Nb tickets',
        compute='_compute_ticket_count',
    )

    @api.depends('ticket_ids')
    def _compute_ticket_count(self):
        for partner in self:
            partner.ticket_count = len(partner.ticket_ids)

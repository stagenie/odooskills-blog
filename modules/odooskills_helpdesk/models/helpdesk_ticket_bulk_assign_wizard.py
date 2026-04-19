from odoo import api, models, fields
from odoo.exceptions import ValidationError


class HelpdeskTicketBulkAssignWizard(models.TransientModel):
    """Wizard d'assignation en masse — opère sur la sélection list view.

    Ouvert via une action contextuelle (binding_model_id='helpdesk.ticket')
    qui apparaît dans le menu "Action" quand l'utilisateur sélectionne
    plusieurs tickets dans la liste.
    """
    _name = 'helpdesk.ticket.bulk.assign.wizard'
    _description = 'Assignation groupée de tickets (wizard)'

    user_id = fields.Many2one(
        comodel_name='res.users',
        string='Nouvel assigné',
        required=True,
        domain="[('share', '=', False)]",
    )
    ticket_ids = fields.Many2many(
        comodel_name='helpdesk.ticket',
        string='Tickets à réassigner',
        required=True,
    )
    ticket_count = fields.Integer(
        string='Nombre',
        compute='_compute_ticket_count',
    )
    notify_assignee = fields.Boolean(
        string='Notifier le nouvel assigné',
        default=True,
    )

    @api.depends('ticket_ids')
    def _compute_ticket_count(self):
        for w in self:
            w.ticket_count = len(w.ticket_ids)

    @api.model
    def default_get(self, fields_list):
        """Récupère la sélection list view via active_ids."""
        vals = super().default_get(fields_list)
        if 'ticket_ids' in fields_list:
            active_ids = self.env.context.get('active_ids', [])
            vals['ticket_ids'] = [(6, 0, active_ids)]
        return vals

    def action_assign(self):
        self.ensure_one()
        if not self.ticket_ids:
            raise ValidationError("Aucun ticket sélectionné.")

        self.ticket_ids.write({'user_id': self.user_id.id})

        if self.notify_assignee:
            for ticket in self.ticket_ids:
                ticket.message_post(
                    body=f"Ticket réassigné à <strong>{self.user_id.name}</strong>",
                    partner_ids=self.user_id.partner_id.ids,
                    subtype_xmlid='mail.mt_comment',
                )

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Réassignation effectuée',
                'message': f"{len(self.ticket_ids)} ticket(s) assigné(s) à {self.user_id.name}.",
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            },
        }

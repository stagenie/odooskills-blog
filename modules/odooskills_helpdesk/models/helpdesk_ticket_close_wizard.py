from odoo import api, models, fields
from odoo.exceptions import ValidationError


class HelpdeskTicketCloseWizard(models.TransientModel):
    """Wizard de clôture de ticket — modèle temporaire.

    Hérite de models.TransientModel : stocké en base mais
    purgé automatiquement par un cron. Durée de vie : le temps
    d'un dialogue utilisateur. Usage typique : wizards.
    """
    _name = 'helpdesk.ticket.close.wizard'
    _description = 'Clôture de ticket helpdesk (wizard)'

    ticket_id = fields.Many2one(
        comodel_name='helpdesk.ticket',
        string='Ticket',
        required=True,
    )
    partner_id = fields.Many2one(
        related='ticket_id.partner_id',
        string='Client',
        readonly=True,
    )
    resolution_reason = fields.Selection(
        selection=[
            ('resolved', 'Résolu'),
            ('not_a_bug', 'Pas un bug / comportement attendu'),
            ('duplicate', 'Duplicata d\'un autre ticket'),
            ('wont_fix', 'Ne sera pas corrigé'),
        ],
        string='Motif de clôture',
        required=True,
        default='resolved',
    )
    duplicate_ticket_id = fields.Many2one(
        comodel_name='helpdesk.ticket',
        string='Ticket doublon',
        domain="[('id', '!=', ticket_id), ('state', '!=', 'done')]",
    )
    resolution_note = fields.Text(
        string='Note de résolution',
        help="Visible par le client si l'envoi de notification est coché.",
    )
    hours_spent = fields.Float(
        string='Heures passées',
        digits=(6, 2),
    )
    notify_partner = fields.Boolean(
        string='Notifier le client',
        default=True,
    )

    @api.model
    def default_get(self, fields_list):
        """Pré-remplit le wizard à partir du contexte.

        Pattern classique : l'action qui ouvre le wizard passe
        `default_ticket_id` dans le contexte ; Odoo l'injecte
        automatiquement. Mais on peut enrichir ici.
        """
        vals = super().default_get(fields_list)
        ticket_id = self.env.context.get('active_id')
        if ticket_id and 'ticket_id' in fields_list and not vals.get('ticket_id'):
            vals['ticket_id'] = ticket_id
        return vals

    def action_close(self):
        """Applique la clôture sur le ticket."""
        self.ensure_one()
        if self.resolution_reason == 'duplicate' and not self.duplicate_ticket_id:
            raise ValidationError(
                "Merci d'indiquer le ticket maître quand le motif est 'Duplicata'."
            )

        note_lines = [
            f"Motif : {dict(self._fields['resolution_reason'].selection).get(self.resolution_reason)}",
        ]
        if self.duplicate_ticket_id:
            note_lines.append(f"Doublon de : {self.duplicate_ticket_id.reference or self.duplicate_ticket_id.display_name}")
        if self.resolution_note:
            note_lines.append(self.resolution_note)

        self.ticket_id.write({
            'state': 'done',
            'resolution_note': '\n'.join(note_lines),
            'hours_spent': self.hours_spent or self.ticket_id.hours_spent,
        })

        if self.notify_partner and self.ticket_id.partner_id:
            self.ticket_id.message_post(
                body=f"<p>Ticket clôturé — <strong>{self.resolution_reason}</strong></p>"
                     f"<p>{self.resolution_note or ''}</p>",
                partner_ids=self.ticket_id.partner_id.ids,
                subtype_xmlid='mail.mt_comment',
            )

        return {'type': 'ir.actions.act_window_close'}

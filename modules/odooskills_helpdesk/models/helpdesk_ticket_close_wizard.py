from odoo import models, fields


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
    resolution_note = fields.Text(string='Note de résolution')

    def action_close(self):
        self.ensure_one()
        self.ticket_id.write({
            'state': 'done',
            'description': (self.ticket_id.description or '') + '\n\nRésolution : ' + (self.resolution_note or ''),
        })
        return {'type': 'ir.actions.act_window_close'}

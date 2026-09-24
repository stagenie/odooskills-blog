from markupsafe import Markup

from odoo import api, fields, models
from odoo.exceptions import UserError


class LibraryLoanExtend(models.TransientModel):
    _name = 'library.loan.extend'
    _description = "Prolonger des emprunts"
    # Explicite : en 20.0, la valeur héritée tombe à 0 dans la tâche de nettoyage.
    _transient_max_hours = 1.0

    loan_ids = fields.Many2many(
        'library.loan',
        string="Emprunts",
        default=lambda self: self._default_loan_ids(),
    )
    days = fields.Integer(string="Jours supplémentaires", default=7, required=True)
    reason = fields.Char(string="Motif")

    @api.model
    def _default_loan_ids(self):
        if self.env.context.get('active_model') != 'library.loan':
            return False
        return self.env['library.loan'].browse(self.env.context.get('active_ids', []))

    def action_extend(self):
        self.ensure_one()
        if self.days <= 0:
            raise UserError(self.env._("Le nombre de jours doit être positif."))
        rendus = self.loan_ids.filtered(lambda e: e.state == 'returned')
        if rendus:
            raise UserError(self.env._(
                "Ces emprunts sont déjà rendus : %(references)s",
                references=", ".join(rendus.mapped('reference')),
            ))
        for emprunt in self.loan_ids:
            emprunt.duration += self.days
            corps = Markup("Prolongé de <b>%s</b> jour(s).") % self.days
            if self.reason:
                corps += Markup(" Motif : %s") % self.reason
            emprunt.message_post(body=corps, message_type='comment', subtype_xmlid='mail.mt_note')
        return {'type': 'ir.actions.act_window_close'}

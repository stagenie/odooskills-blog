from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class LibraryLoan(models.Model):
    _name = 'library.loan'
    _description = "Emprunt"
    _order = 'date_out desc, id desc'

    member_id = fields.Many2one(
        'library.member',
        string="Adhérent",
        required=True,
        ondelete='cascade',
    )
    copy_id = fields.Many2one(
        'library.copy',
        string="Exemplaire",
        required=True,
        ondelete='restrict',
    )
    date_out = fields.Date(
        string="Emprunté le",
        required=True,
        default=fields.Date.context_today,
    )
    duration = fields.Integer(string="Durée (jours)", default=14, required=True)
    date_due = fields.Date(
        string="À rendre le",
        compute='_compute_date_due',
        store=True,
    )
    date_return = fields.Date(string="Rendu le", readonly=True, copy=False)
    state = fields.Selection(
        [
            ('ongoing', "En cours"),
            ('returned', "Rendu"),
        ],
        string="État",
        default='ongoing',
        required=True,
    )
    is_late = fields.Boolean(string="En retard", compute='_compute_is_late')

    @api.depends('date_out', 'duration')
    def _compute_date_due(self):
        for loan in self:
            if loan.date_out:
                loan.date_due = loan.date_out + relativedelta(days=loan.duration)
            else:
                loan.date_due = False

    @api.depends('date_due', 'date_return', 'state')
    def _compute_is_late(self):
        today = fields.Date.context_today(self)
        for loan in self:
            fin = loan.date_return or today
            loan.is_late = bool(loan.date_due) and loan.state == 'ongoing' and fin > loan.date_due

    @api.constrains('copy_id', 'state')
    def _check_copy_available(self):
        for loan in self:
            if loan.state != 'ongoing':
                continue
            autres = self.search_count([
                ('copy_id', '=', loan.copy_id.id),
                ('state', '=', 'ongoing'),
                ('id', '!=', loan.id),
            ])
            if autres:
                raise ValidationError(
                    f"L'exemplaire {loan.copy_id.name} est déjà emprunté."
                )

    @api.model_create_multi
    def create(self, vals_list):
        emprunts = super().create(vals_list)
        emprunts.filtered(lambda e: e.state == 'ongoing').copy_id.state = 'borrowed'
        return emprunts

    def action_return(self):
        for loan in self:
            if loan.state == 'returned':
                raise ValidationError("Cet emprunt est déjà clos.")
            loan.write({
                'state': 'returned',
                'date_return': fields.Date.context_today(loan),
            })
            loan.copy_id.state = 'available'

    @api.depends('member_id.card_number', 'copy_id.name')
    def _compute_display_name(self):
        for loan in self:
            loan.display_name = f"{loan.copy_id.name} → {loan.member_id.card_number}"

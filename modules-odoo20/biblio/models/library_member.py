from odoo import api, fields, models


class LibraryMember(models.Model):
    _name = 'library.member'
    _description = "Adhérent"
    _inherits = {'res.partner': 'partner_id'}
    _order = 'card_number'

    partner_id = fields.Many2one(
        'res.partner',
        string="Partenaire",
        required=True,
        ondelete='cascade',
    )
    card_number = fields.Char(string="Numéro de carte", required=True, copy=False)
    join_date = fields.Date(
        string="Date d'adhésion",
        default=fields.Date.context_today,
    )

    loan_ids = fields.One2many('library.loan', 'member_id', string="Emprunts")
    loan_count = fields.Integer(
        string="Nombre d'emprunts",
        compute='_compute_loan_count',
        store=True,
    )
    late_loan_count = fields.Integer(
        string="Nombre de retards",
        compute='_compute_late_loan_count',
    )

    _card_number_unique = models.Constraint(
        'UNIQUE(card_number)',
        "Ce numéro de carte est déjà attribué à un autre adhérent.",
    )

    @api.depends('loan_ids')
    def _compute_loan_count(self):
        for member in self:
            member.loan_count = len(member.loan_ids)

    @api.depends('loan_ids.is_late')
    def _compute_late_loan_count(self):
        for member in self:
            member.late_loan_count = len(member.loan_ids.filtered('is_late'))

    def action_view_loans(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f"Emprunts de {self.name}",
            'res_model': 'library.loan',
            'view_mode': 'list,form',
            'domain': [('member_id', '=', self.id)],
            'context': {'default_member_id': self.id},
        }

    def action_view_late_loans(self):
        self.ensure_one()
        action = self.action_view_loans()
        action['name'] = f"Retards de {self.name}"
        action['domain'] = [('member_id', '=', self.id), ('is_late', '=', True)]
        return action

    @api.depends('card_number', 'partner_id.name')
    def _compute_display_name(self):
        for member in self:
            member.display_name = f"{member.name} ({member.card_number})"

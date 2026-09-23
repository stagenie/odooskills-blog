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

    _card_number_unique = models.Constraint(
        'UNIQUE(card_number)',
        "Ce numéro de carte est déjà attribué à un autre adhérent.",
    )

    @api.depends('card_number', 'partner_id.name')
    def _compute_display_name(self):
        for member in self:
            member.display_name = f"{member.name} ({member.card_number})"

from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    library_loan_ids = fields.One2many(
        'library.loan',
        'partner_id',
        string="Emprunts du contact",
        groups='biblio.group_library_desk',
    )
    library_loan_count = fields.Integer(
        string="Nombre d'emprunts du contact",
        compute='_compute_library_loan_count',
        groups='biblio.group_library_desk',
    )

    @api.depends('library_loan_ids')
    def _compute_library_loan_count(self):
        for partner in self:
            partner.library_loan_count = len(partner.library_loan_ids)

    def action_view_library_loans(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._("Emprunts de %(nom)s", nom=self.name),
            'res_model': 'library.loan',
            'view_mode': 'list,form',
            'domain': [('partner_id', '=', self.id)],
        }

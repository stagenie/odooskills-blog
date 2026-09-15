from odoo import api, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    @api.model_create_multi
    def create(self, vals_list):
        companies = super().create(vals_list)
        companies._odooskills_create_work_order_sequence()
        return companies

    def _odooskills_create_work_order_sequence(self):
        Sequence = self.env['ir.sequence'].sudo()
        for company in self:
            if Sequence.search_count([
                ('code', '=', 'odooskills.work.order'),
                ('company_id', '=', company.id),
            ]):
                continue
            Sequence.create({
                'name': f"Bons d'intervention — {company.name}",
                'code': 'odooskills.work.order',
                'company_id': company.id,
                'prefix': 'BI/%(year)s/',
                'padding': 4,
            })

from odoo import api, fields, models


class WorkOrder(models.Model):
    _name = 'odooskills.work.order'
    _description = "Bon d'intervention"
    _check_company_auto = True

    name = fields.Char(string="Référence", readonly=True, copy=False, default='/')
    company_id = fields.Many2one(
        'res.company', string="Société", required=True, index=True,
        default=lambda self: self.env.company,
    )
    site_id = fields.Many2one(
        'odooskills.work.site', string="Site", required=True, check_company=True,
    )
    partner_id = fields.Many2one('res.partner', string="Client", check_company=True)
    hours = fields.Float(string="Heures")
    hourly_rate = fields.Float(
        string="Taux horaire", compute='_compute_hourly_rate', store=True, readonly=False,
    )
    date_deadline = fields.Date(string="Échéance")
    state = fields.Selection(
        [('draft', "Brouillon"), ('done', "Terminé"), ('late', "En retard")],
        string="État", default='draft', required=True,
    )

    @api.depends('partner_id', 'company_id')
    def _compute_hourly_rate(self):
        for order in self:
            # La valeur company_dependent est lue pour la société du bon,
            # pas pour la société active de l'utilisateur.
            partner = order.partner_id.with_company(order.company_id)
            order.hourly_rate = partner.odooskills_hourly_rate

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', '/') == '/':
                company = self.env['res.company'].browse(vals.get('company_id')) or self.env.company
                vals['name'] = self.env['ir.sequence'].sudo().with_company(company).next_by_code(
                    'odooskills.work.order') or '/'
        return super().create(vals_list)

    @api.model
    def _cron_mark_late(self):
        today = fields.Date.context_today(self)
        for company in self.env['res.company'].search([]):
            late = self.with_company(company).search([
                ('company_id', '=', company.id),
                ('state', '=', 'draft'),
                ('date_deadline', '<', today),
            ])
            late.write({'state': 'late'})

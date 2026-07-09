from odoo import api, fields, models


class AffiliateCommission(models.Model):
    _name = 'oski.affiliate.commission'
    _description = "Commission d'affiliation"
    _order = 'date desc, id desc'

    program_id = fields.Many2one(
        'oski.affiliate.program', string='Programme',
        required=True, ondelete='cascade', index=True)
    date = fields.Date(
        string='Date', required=True, default=fields.Date.context_today)
    period = fields.Char(
        string='Période', compute='_compute_period', store=True,
        help="Mois de la commission (AAAA-MM), pour les regroupements.")
    amount = fields.Monetary(
        string='Montant', currency_field='currency_id', required=True)
    currency_id = fields.Many2one(
        'res.currency', string='Devise', required=True,
        default=lambda self: self.env.company.currency_id)
    company_currency_id = fields.Many2one(
        'res.currency', related='program_id.company_currency_id', store=True)
    amount_company = fields.Monetary(
        string='Montant (devise société)', currency_field='company_currency_id',
        compute='_compute_amount_company', store=True)
    status = fields.Selection(
        [('pending', 'En attente'), ('confirmed', 'Confirmée'), ('paid', 'Payée')],
        string='Statut', default='pending', required=True)
    reference = fields.Char(string='Référence')
    site = fields.Char(related='program_id.site', store=True, string='Site')
    note = fields.Char(string='Note')

    @api.depends('date')
    def _compute_period(self):
        for rec in self:
            rec.period = rec.date.strftime('%Y-%m') if rec.date else False

    @api.depends('amount', 'currency_id', 'date', 'program_id.company_currency_id')
    def _compute_amount_company(self):
        for rec in self:
            comp_cur = rec.program_id.company_currency_id or rec.currency_id
            if rec.currency_id and comp_cur and rec.currency_id != comp_cur:
                rec.amount_company = rec.currency_id._convert(
                    rec.amount, comp_cur, self.env.company,
                    rec.date or fields.Date.context_today(rec))
            else:
                rec.amount_company = rec.amount

    @api.depends('program_id', 'date', 'amount', 'currency_id')
    def _compute_display_name(self):
        for rec in self:
            parts = [rec.program_id.name or '']
            if rec.date:
                parts.append(rec.date.strftime('%d/%m/%Y'))
            rec.display_name = ' — '.join(p for p in parts if p) or 'Commission'

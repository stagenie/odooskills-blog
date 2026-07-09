from odoo import api, fields, models


class AffiliateProgram(models.Model):
    _name = 'oski.affiliate.program'
    _description = "Programme d'affiliation"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    name = fields.Char(string='Nom du programme', required=True, tracking=True)
    active = fields.Boolean(default=True)
    status = fields.Selection(
        [('active', 'Actif'), ('paused', 'En pause'), ('closed', 'Fermé')],
        string='Statut', default='active', required=True, tracking=True)
    site = fields.Char(
        string='Site(s)', default='OdooSkills',
        help="Site(s) où ce programme est utilisé — texte libre "
             "(ex. « OdooSkills », « AISkillsPro », « OdooSkills, monsite.com »).")
    tag_ids = fields.Many2many('oski.affiliate.tag', string='Catégories')

    currency_id = fields.Many2one(
        'res.currency', string='Devise', required=True,
        default=lambda self: self.env.company.currency_id)
    company_currency_id = fields.Many2one(
        'res.currency', string='Devise société', readonly=True,
        default=lambda self: self.env.company.currency_id)

    # Compte & liens
    signup_url = fields.Char(string="URL d'inscription")
    dashboard_url = fields.Char(string='URL tableau de bord')
    referral_link = fields.Char(string='Lien affilié principal')
    link_ids = fields.One2many(
        'oski.affiliate.link', 'program_id', string="Liens d'affiliation")
    link_count = fields.Integer(string='Nb liens', compute='_compute_link_count')
    login_username = fields.Char(string='Login / email')
    credentials_ref = fields.Char(
        string='Emplacement du mot de passe',
        help="Où retrouver le mot de passe (ex. « Bitwarden > Amazon »). "
             "NE JAMAIS écrire le mot de passe en clair ici.")
    contact_email = fields.Char(string='Contact du programme')

    # Commission
    commission_model = fields.Selection(
        [('percent', 'Pourcentage'), ('fixed', 'Montant fixe'), ('tiered', 'Paliers')],
        string='Modèle de commission', default='percent')
    default_rate = fields.Float(string='Taux / montant par défaut')
    payment_method = fields.Char(string='Méthode de paiement')
    payout_threshold = fields.Monetary(
        string='Seuil de paiement', currency_field='currency_id')

    note = fields.Html(string='Notes')
    commission_ids = fields.One2many(
        'oski.affiliate.commission', 'program_id', string='Commissions')

    # Statistiques (converties en devise société)
    commission_count = fields.Integer(
        string='Nb commissions', compute='_compute_stats')
    total_earned = fields.Monetary(
        string='Total gagné', compute='_compute_stats',
        currency_field='company_currency_id')
    total_pending = fields.Monetary(
        string='En attente', compute='_compute_stats',
        currency_field='company_currency_id')
    total_paid = fields.Monetary(
        string='Payé', compute='_compute_stats',
        currency_field='company_currency_id')
    last_commission_date = fields.Date(
        string='Dernière commission', compute='_compute_stats')

    @api.depends('commission_ids.amount_company', 'commission_ids.status', 'commission_ids.date')
    def _compute_stats(self):
        for prog in self:
            comms = prog.commission_ids
            prog.commission_count = len(comms)
            prog.total_earned = sum(comms.mapped('amount_company'))
            prog.total_pending = sum(
                comms.filtered(lambda c: c.status == 'pending').mapped('amount_company'))
            prog.total_paid = sum(
                comms.filtered(lambda c: c.status == 'paid').mapped('amount_company'))
            dates = comms.mapped('date')
            prog.last_commission_date = max(dates) if dates else False

    @api.depends('link_ids')
    def _compute_link_count(self):
        for prog in self:
            prog.link_count = len(prog.link_ids)

    def action_view_commissions(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Commissions — %s' % self.name,
            'res_model': 'oski.affiliate.commission',
            'view_mode': 'list,form,pivot,graph',
            'domain': [('program_id', '=', self.id)],
            'context': {
                'default_program_id': self.id,
                'default_currency_id': self.currency_id.id,
            },
        }

    def action_open_dashboard(self):
        self.ensure_one()
        if not self.dashboard_url:
            return False
        return {'type': 'ir.actions.act_url', 'url': self.dashboard_url, 'target': 'new'}

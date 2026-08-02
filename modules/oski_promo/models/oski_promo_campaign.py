from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class OskiPromoCampaign(models.Model):
    _name = 'oski.promo.campaign'
    _description = 'Campagne promotionnelle OdooSkills'
    _order = 'date_start desc, id desc'

    name = fields.Char(
        string='Nom interne', required=True,
        help="Repère de gestion. Ex. « Été 2026 ».")
    label_public = fields.Char(
        string='Libellé public', required=True,
        help="Texte affiché sur le site : bandeau et compte à rebours.")
    date_start = fields.Datetime(string='Début', required=True)
    date_end = fields.Datetime(string='Fin', required=True)
    discount_percent = fields.Float(
        string='Remise (%)', default=0.0,
        help="Sert uniquement à pré-remplir les lignes. Les prix restent éditables.")
    line_ids = fields.One2many(
        'oski.promo.line', 'campaign_id', string='Produits en promotion')
    applied = fields.Boolean(
        string='Appliquée', readonly=True, copy=False,
        help="Les items de liste de prix ont été générés.")
    state = fields.Selection(
        [('draft', 'Brouillon'), ('scheduled', 'Programmée'),
         ('running', 'En cours'), ('done', 'Terminée')],
        string='État', compute='_compute_state',
        help="Calculé depuis les dates : rien ne l'écrit, donc rien ne peut "
             "échouer à l'écrire. C'est ce qui rend l'extinction automatique.")
    active = fields.Boolean(default=True)

    @api.depends('applied', 'date_start', 'date_end')
    def _compute_state(self):
        now = fields.Datetime.now()
        for rec in self:
            if not rec.applied:
                rec.state = 'draft'
            elif rec.date_end and rec.date_end <= now:
                rec.state = 'done'
            elif rec.date_start and rec.date_start > now:
                rec.state = 'scheduled'
            else:
                rec.state = 'running'

    @api.constrains('date_start', 'date_end')
    def _check_dates(self):
        for rec in self:
            if rec.date_start and rec.date_end and rec.date_end <= rec.date_start:
                raise ValidationError(
                    "La fin de campagne doit être postérieure à son début.")

    def action_generate_lines(self):
        """Recrée une ligne par produit tarifé, au prix courant remisé.
        Les prix restent éditables ligne à ligne après coup."""
        Product = self.env['product.template']
        for rec in self:
            if rec.applied:
                raise UserError(
                    "Campagne déjà appliquée : annulez-la avant de régénérer "
                    "ses lignes, sinon les prix affichés et les items de liste "
                    "de prix divergeraient.")
            rec.line_ids.unlink()
            facteur = 1.0 - (rec.discount_percent / 100.0)
            produits = Product.search([('ebook_ids', '!=', False)])
            rec.line_ids = [
                (0, 0, {
                    'product_tmpl_id': produit.id,
                    'price_promo': round(
                        (produit.oski_price_launch or produit.oski_price_regular)
                        * facteur, 2),
                })
                for produit in produits
            ]

    def oski_deadline_iso(self):
        """Échéance au format ISO 8601 UTC, consommée par le JS du compteur."""
        self.ensure_one()
        if not self.date_end:
            return ''
        return fields.Datetime.to_string(self.date_end).replace(' ', 'T') + 'Z'

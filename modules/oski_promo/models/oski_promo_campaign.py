from datetime import timedelta

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

    def write(self, vals):
        if 'date_start' in vals or 'date_end' in vals:
            verrouillees = self.filtered('applied')
            if verrouillees:
                raise UserError(
                    "Campagne déjà appliquée (%s) : impossible d'en changer "
                    "les dates. Annulez-la d'abord (repassez « Appliquée » à "
                    "faux), sinon les items de prix resteraient sur les "
                    "anciennes bornes pendant que le compteur et le bandeau "
                    "afficheraient les nouvelles." % ', '.join(verrouillees.mapped('name')))
        return super().write(vals)

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

    def _pricelist(self):
        """Liste de prix EUR déclarée en paramètre système."""
        ICP = self.env['ir.config_parameter'].sudo()
        pl_id = int(ICP.get_param('oski.pricing.eur_pricelist_id') or 0)
        return self.env['product.pricelist'].browse(pl_id).exists()

    def _check_no_overlap(self):
        """Deux campagnes appliquées sur un même produit à la même période
        produiraient deux items actifs, donc un prix indéterminé — premier
        filet, basé sur les dates des deux campagnes.

        Second filet, plus large : action_apply() purge TOUS les items du
        produit (quelle que soit la campagne qui les a posés) et les items
        créés couvrent −∞ → +∞. Donc une campagne déjà appliquée et non
        terminée (date_end dans le futur) doit aussi bloquer, même sans
        chevauchement de période : sinon son application serait écrasée en
        silence par une campagne future sur le même produit."""
        self.ensure_one()
        now = fields.Datetime.now()
        chevauchantes = self.search([
            ('id', '!=', self.id), ('applied', '=', True),
            ('date_start', '<=', self.date_end), ('date_end', '>=', self.date_start),
        ])
        non_terminees = self.search([
            ('id', '!=', self.id), ('applied', '=', True),
            ('date_end', '>', now),
        ])
        autres = chevauchantes | non_terminees
        collision = autres.line_ids.product_tmpl_id & self.line_ids.product_tmpl_id
        if collision:
            conflit = autres.filtered(
                lambda c: c.line_ids.product_tmpl_id & self.line_ids.product_tmpl_id)[:1]
            raise UserError(
                "Campagne « %s » déjà appliquée et non terminée sur : %s. "
                "Annulez-la d'abord (repassez « Appliquée » à faux) avant "
                "d'appliquer celle-ci, sinon son application écraserait en "
                "silence les items de prix encore actifs et le prix affiché "
                "deviendrait indéterminé." % (
                    conflit.name,
                    ', '.join(collision.mapped('display_name'))))

    def action_apply(self):
        """Couvre toute la ligne du temps par trois items exclusifs :
        courant → promo → courant. Le repli est le prix COURANT, pas le barré."""
        Item = self.env['product.pricelist.item']
        for rec in self:
            if not rec.line_ids:
                raise UserError("Campagne sans ligne : rien à appliquer.")
            pricelist = rec._pricelist()
            if not pricelist:
                raise UserError(
                    "Liste de prix EUR introuvable : renseignez le paramètre "
                    "système « oski.pricing.eur_pricelist_id ».")
            rec._check_no_overlap()
            une_seconde = timedelta(seconds=1)
            for line in rec.line_ids:
                produit = line.product_tmpl_id
                courant = produit.oski_price_launch or produit.oski_price_regular
                # On ne purge que les items du produit : l'item global de la
                # liste (sans produit) n'appartient pas à la campagne.
                Item.search([('pricelist_id', '=', pricelist.id),
                             ('product_tmpl_id', '=', produit.id)]).unlink()
                base = {'pricelist_id': pricelist.id,
                        'product_tmpl_id': produit.id,
                        'applied_on': '1_product', 'compute_price': 'fixed'}
                Item.create({**base, 'fixed_price': courant,
                             'date_end': rec.date_start - une_seconde})
                Item.create({**base, 'fixed_price': line.price_promo,
                             'date_start': rec.date_start,
                             'date_end': rec.date_end})
                Item.create({**base, 'fixed_price': courant,
                             'date_start': rec.date_end + une_seconde})
            rec.applied = True

    def oski_deadline_iso(self):
        """Échéance au format ISO 8601 UTC, consommée par le JS du compteur."""
        self.ensure_one()
        if not self.date_end:
            return ''
        return fields.Datetime.to_string(self.date_end).replace(' ', 'T') + 'Z'

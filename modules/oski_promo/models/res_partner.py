from odoo import api, fields, models

from .product_template import oski_fmt

MOIS_FR = ['janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet', 'août',
           'septembre', 'octobre', 'novembre', 'décembre']


def _oski_date_fr(d):
    """31/12/2026 → « 31 décembre 2026 » (1er pour le premier du mois)."""
    jour = '1er' if d.day == 1 else str(d.day)
    return '%s %s %s' % (jour, MOIS_FR[d.month - 1], d.year)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # Codes personnels envoyés à ce client (voir loyalty.card.oski_partner_id).
    # Les champs calculés donnent au publipostage (modèle res.partner) le code
    # encore utilisable : {{ object.oski_coupon_code }}, {{ object.oski_coupon_label }},
    # {{ object.oski_coupon_price_fmt }}, {{ object.oski_coupon_expiration }}.
    oski_coupon_ids = fields.One2many(
        'loyalty.card', 'oski_partner_id', string='Codes personnels')
    oski_coupon_code = fields.Char(
        string='Code personnel en cours', compute='_compute_oski_coupon',
        help="Dernier code personnel encore utilisable (programme actif, non "
             "expiré, points suffisants). Vide sinon.")
    oski_coupon_label = fields.Char(
        string='Code personnel — libellé', compute='_compute_oski_coupon',
        help="Description de la récompense du code en cours.")
    oski_coupon_price_fmt = fields.Char(
        string='Code personnel — prix net', compute='_compute_oski_coupon',
        help="Prix net garanti du code en cours, formaté (ex. « 5,90 € »). "
             "Vide si la récompense n'a pas de prix net.")
    oski_coupon_discount_fmt = fields.Char(
        string='Code personnel — remise', compute='_compute_oski_coupon',
        help="Remise de la récompense du code en cours, formatée (ex. « −90 % »). "
             "Vide si la récompense n'est pas une remise en pourcentage.")
    oski_coupon_expiration = fields.Date(
        string='Code personnel — expire le', compute='_compute_oski_coupon')
    oski_coupon_expiration_fmt = fields.Char(
        string='Code personnel — expire le (texte)', compute='_compute_oski_coupon',
        help="Date d'expiration en toutes lettres pour les courriels (ex. « 31 décembre 2026 »).")

    def _oski_usable_coupon(self):
        """La carte la plus récente encore consommable, ou un recordset vide."""
        self.ensure_one()
        today = fields.Date.context_today(self)

        def usable(card):
            program = card.program_id
            if not (card.active and program.active and program.reward_ids):
                return False
            if card.expiration_date and card.expiration_date < today:
                return False
            return card.points >= min(program.reward_ids.mapped('required_points'))

        cards = self.oski_coupon_ids.filtered(usable)
        return cards.sorted(key=lambda c: c.id, reverse=True)[:1]

    @api.depends('oski_coupon_ids.points', 'oski_coupon_ids.active',
                 'oski_coupon_ids.expiration_date', 'oski_coupon_ids.program_id.active')
    def _compute_oski_coupon(self):
        for partner in self:
            card = partner._oski_usable_coupon()
            reward = card.program_id.reward_ids[:1]
            partner.oski_coupon_code = card.code or False
            partner.oski_coupon_label = reward.description or False
            partner.oski_coupon_expiration = card.expiration_date or False
            partner.oski_coupon_expiration_fmt = (
                _oski_date_fr(card.expiration_date) if card.expiration_date else False)
            if reward.reward_type == 'discount' and reward.discount_mode == 'percent' and reward.discount:
                partner.oski_coupon_discount_fmt = '−%s %%' % oski_fmt(reward.discount)
            else:
                partner.oski_coupon_discount_fmt = False
            if reward.oski_net_price:
                partner.oski_coupon_price_fmt = '%s %s' % (
                    oski_fmt(reward.oski_net_price), reward.currency_id.symbol or '')
            else:
                partner.oski_coupon_price_fmt = False

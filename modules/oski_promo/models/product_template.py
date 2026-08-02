from odoo import fields, models

# Tolérance de comparaison entre deux montants en euros. Un centime pèse
# 0,01 : rester en dessous évite qu'un flottant issu de la liste de prix
# (16.799999999999997) passe pour différent de sa valeur nominale.
OSKI_EPSILON = 0.005


def oski_fmt(value):
    """Montant à la française, sans décimale inutile. 24.0 → '24' ; 16.8 → '16,80'."""
    if abs(value - round(value)) < 0.005:
        return '%d' % round(value)
    return ('%.2f' % value).replace('.', ',')


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def _oski_running_campaign(self):
        """Campagne appliquée et en cours couvrant ce produit, sinon vide."""
        self.ensure_one()
        now = fields.Datetime.now()
        line = self.env['oski.promo.line'].sudo().search([
            ('product_tmpl_id', '=', self.id),
            ('campaign_id.applied', '=', True),
            ('campaign_id.active', '=', True),
            ('campaign_id.date_start', '<=', now),
            ('campaign_id.date_end', '>=', now),
        ], limit=1)
        return line.campaign_id

    def _oski_pricelist(self):
        """Liste de prix EUR déclarée en paramètre système, ou vide."""
        ICP = self.env['ir.config_parameter'].sudo()
        pl_id = int(ICP.get_param('oski.pricing.eur_pricelist_id') or 0)
        return self.env['product.pricelist'].sudo().browse(pl_id).exists()

    def _oski_payer_courant(self):
        """(prix réellement facturé, prix courant hors promotion).

        `payer` est lu depuis la liste de prix, jamais depuis un champ :
        c'est le montant que la caisse encaissera. `courant` est le prix
        hors promotion, celui qui reprend la main à l'échéance.
        """
        self.ensure_one()
        pricelist = self._oski_pricelist()
        variant = self.product_variant_id
        courant = self.oski_price_launch or self.oski_price_regular
        if pricelist and variant:
            payer = pricelist._get_product_price(variant, 1.0)
        else:
            payer = courant
        return payer, courant

    def _oski_promo_effective(self):
        """Le prix facturé est-il RÉELLEMENT inférieur au prix courant ?

        Un booléen `applied` sur la campagne ne prouve rien : le module
        voisin oski_ebook_lifecycle écrit le même espace d'items de liste
        de prix avec la même purge. Rejouer son script de tarification
        pendant une campagne efface les items promotionnels sans rien
        écrire côté campagne — `applied` resterait vrai et le site
        continuerait d'annoncer une remise que la caisse n'accorde plus.
        On croit donc au prix, jamais au drapeau.
        """
        self.ensure_one()
        payer, courant = self._oski_payer_courant()
        return payer < courant - OSKI_EPSILON

    def _oski_price_info(self):
        """Tout ce dont une surface d'affichage a besoin, en une lecture.

        `payer` vient de la liste de prix, jamais d'un champ : après
        l'échéance il vaut le prix courant sans qu'aucun code ici ne
        connaisse la notion de promotion.

        `promo`, `deadline_iso` et `label` ne sont vrais qu'ensemble, et
        seulement si le prix facturé est effectivement remisé : jamais de
        bandeau, de libellé ni de compteur au-dessus d'un plein tarif.
        """
        self.ensure_one()
        payer, courant = self._oski_payer_courant()
        campaign = self._oski_running_campaign()
        promo = bool(campaign) and payer < courant - OSKI_EPSILON
        return {
            'barre': self.oski_price_regular,
            'payer': payer,
            'after': courant,
            'barre_fmt': oski_fmt(self.oski_price_regular),
            'payer_fmt': oski_fmt(payer),
            'after_fmt': oski_fmt(courant),
            'promo': promo,
            'deadline_iso': campaign.oski_deadline_iso() if promo else '',
            'label': campaign.label_public if promo else '',
        }

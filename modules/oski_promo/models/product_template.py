from odoo import fields, models


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

    def _oski_price_info(self):
        """Tout ce dont une surface d'affichage a besoin, en une lecture.

        `payer` vient de la liste de prix, jamais d'un champ : après
        l'échéance il vaut le prix courant sans qu'aucun code ici ne
        connaisse la notion de promotion.
        """
        self.ensure_one()
        ICP = self.env['ir.config_parameter'].sudo()
        pl_id = int(ICP.get_param('oski.pricing.eur_pricelist_id') or 0)
        pricelist = self.env['product.pricelist'].sudo().browse(pl_id).exists()
        variant = self.product_variant_id
        courant = self.oski_price_launch or self.oski_price_regular
        if pricelist and variant:
            payer = pricelist._get_product_price(variant, 1.0)
        else:
            payer = courant
        campaign = self._oski_running_campaign()
        return {
            'barre': self.oski_price_regular,
            'payer': payer,
            'after': courant,
            'barre_fmt': oski_fmt(self.oski_price_regular),
            'payer_fmt': oski_fmt(payer),
            'after_fmt': oski_fmt(courant),
            'promo': bool(campaign),
            'deadline_iso': campaign.oski_deadline_iso() if campaign else '',
            'label': campaign.label_public if campaign else '',
        }

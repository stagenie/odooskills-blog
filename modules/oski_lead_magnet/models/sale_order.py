from odoo import fields, models
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _oski_applied_welcome_offers(self):
        """oski.welcome.offer dont le coupon (loyalty.card) est appliqué à la commande."""
        self.ensure_one()
        applied = self.applied_coupon_ids
        if not applied:
            return self.env['oski.welcome.offer']
        return self.env['oski.welcome.offer'].sudo().search([
            ('coupon_id', 'in', applied.ids),
        ])

    def _oski_expired_welcome_cards(self):
        """loyalty.card appliquées liées à une offre bienvenue expirée."""
        self.ensure_one()
        now = fields.Datetime.now()
        offers = self._oski_applied_welcome_offers()
        bad = offers.filtered(
            lambda o: o.state == 'expired' or (o.deadline and o.deadline < now))
        return bad.coupon_id

    def _action_confirm(self):
        for order in self:
            bad = order._oski_expired_welcome_cards()
            if bad:
                raise UserError(
                    "La remise de bienvenue -50% a expiré (délai de 72 h dépassé). "
                    "Retirez le code pour poursuivre au tarif normal.")
        result = super()._action_confirm()
        now = fields.Datetime.now()
        for order in self:
            offers = order._oski_applied_welcome_offers()
            valid = offers.filtered(
                lambda o: o.state in ('active', 'dormant')
                and not (o.deadline and o.deadline < now))
            if valid:
                valid.write({'state': 'used'})
        return result

import logging

from odoo import models
from odoo.tools import email_normalize

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _action_confirm(self):
        res = super()._action_confirm()
        self._apply_ebook_lifecycle()
        return res

    def _apply_ebook_lifecycle(self):
        """À la confirmation d'une commande payée : tague le partner avec les
        catégories des ebooks possédés (+ tier), et passe opt_out=True sur ses
        souscriptions aux listes extrait correspondantes. Idempotent.

        sudo sur mailing.subscription : la confirmation peut être faite par un
        vendeur sans droits Marketing (ou en public via le paiement web). L'opt_out
        est un effet automatique de l'achat, pas un accès utilisateur aux données."""
        Subscription = self.env['mailing.subscription'].sudo()
        for order in self:
            products = order.order_line.product_id
            ebooks = products.ebook_ids
            if not ebooks:
                continue
            tiers = products.lifecycle_tier_category_id
            cats = ebooks.partner_category_id | tiers
            partner = order.partner_id
            if cats:
                partner.write({'category_id': [(4, c.id) for c in cats]})

            email = email_normalize(partner.email) if partner.email else False
            if not email:
                _logger.info(
                    'ebook lifecycle: partner %s sans email, opt_out sauté', partner.id)
                continue

            for ebook in ebooks:
                if not ebook.extract_list_id:
                    continue
                subs = Subscription.search([
                    ('list_id', '=', ebook.extract_list_id.id),
                ]).filtered(
                    lambda s: email_normalize(s.contact_id.email or '') == email)
                to_optout = subs.filtered(lambda s: not s.opt_out)
                if to_optout:
                    to_optout.write({'opt_out': True})

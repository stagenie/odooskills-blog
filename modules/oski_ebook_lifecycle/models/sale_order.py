import logging

from odoo import fields, models
from odoo.tools import email_normalize

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    ebook_delivery_sent = fields.Boolean(
        string="Email ebook envoyé", default=False, copy=False,
        help="Garde d'idempotence : empêche le renvoi de l'email de livraison.")

    def _action_confirm(self):
        res = super()._action_confirm()
        self._apply_ebook_lifecycle()
        self._send_ebook_delivery_email()
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

    def _send_ebook_delivery_email(self):
        """Envoie l'email de livraison brandé (liens download directs + portail).
        Déclenché sur confirm => payment-agnostic. Idempotent via ebook_delivery_sent.
        N'envoie que si la commande contient au moins un ebook livrable."""
        template = self.env.ref(
            'oski_ebook_lifecycle.mail_template_ebook_delivery',
            raise_if_not_found=False)
        if not template:
            return
        for order in self:
            if order.ebook_delivery_sent:
                continue
            if not order.order_line.product_id.ebook_ids:
                continue
            template.send_mail(order.id, force_send=False)
            order.ebook_delivery_sent = True

import logging

from markupsafe import Markup

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
        """À la confirmation d'une commande payée : tague le client avec les
        catégories des ebooks possédés (+ tier), et passe opt_out=True sur ses
        souscriptions aux listes extrait correspondantes. Idempotent.

        « Le client », ce n'est pas seulement order.partner_id : un achat en
        invité crée toujours une fiche neuve (website_sale, panier anonyme),
        même quand le courriel est déjà connu. Les étiquettes vont donc aussi
        sur les autres fiches du même client (_oski_same_customer_partners) et
        sur les mailing.contact de toutes ses adresses : sinon l'acheteur reste
        « non client » pour les campagnes. La commande n'est PAS rattachée à
        l'ancienne fiche : un visiteur anonyme qui tape le courriel d'un autre
        verrait l'adresse de cette fiche sur la page de confirmation. Le doublon
        est signalé par une activité, la fusion reste manuelle.

        sudo sur res.partner / mailing.contact / mailing.subscription : la
        confirmation peut être faite par un vendeur sans droits Marketing (ou en
        public via le paiement web). Ce sont des effets automatiques de l'achat,
        pas un accès utilisateur aux données."""
        Subscription = self.env['mailing.subscription'].sudo()
        MailingContact = self.env['mailing.contact'].sudo()
        for order in self:
            products = order.order_line.product_id
            ebooks = products.ebook_ids
            if not ebooks:
                continue
            tiers = products.lifecycle_tier_category_id
            cats = ebooks.partner_category_id | tiers
            partner = order.partner_id.sudo()
            others = order._oski_same_customer_partners()
            if cats:
                partner.write({'category_id': [(4, c.id) for c in cats]})
                if others:
                    others.write({'category_id': [(4, c.id) for c in cats]})
            if others:
                order._oski_flag_duplicate_customer(others)

            emails = {email_normalize(p.email) for p in partner | others if p.email}
            emails.discard(False)
            if not emails:
                _logger.info(
                    'ebook lifecycle: partner %s sans email, opt_out sauté', partner.id)
                continue

            if cats:
                contacts = MailingContact.search([('email_normalized', 'in', list(emails))])
                if contacts:
                    contacts.write({'tag_ids': [(4, c.id) for c in cats]})

            for ebook in ebooks:
                if not ebook.extract_list_id:
                    continue
                subs = Subscription.search([
                    ('list_id', '=', ebook.extract_list_id.id),
                    ('opt_out', '=', False),
                ]).filtered(
                    lambda s: email_normalize(s.contact_id.email or '') in emails)
                if subs:
                    subs.write({'opt_out': True})

    def _oski_same_customer_partners(self):
        """Autres fiches (sociétés commerciales) du même client que l'acheteur.

        Ici : même courriel normalisé. Étendu par oski_promo (destinataire du
        code de fidélité utilisé, quand le client a payé sous une autre adresse).
        Retourne un recordset sudo, sans la fiche de l'acheteur."""
        self.ensure_one()
        buyer = self.partner_id.commercial_partner_id
        email = email_normalize(self.partner_id.email or '')
        if not email:
            return self.env['res.partner'].sudo()
        same = self.env['res.partner'].sudo().search([
            ('email_normalized', '=', email),
            ('id', 'not in', buyer.ids),
        ])
        return same.commercial_partner_id - buyer

    def _oski_flag_duplicate_customer(self, others):
        """Activité « à fusionner » sur la commande, une seule fois. Fusion via
        Contacts > Action > Fusionner (mode développeur)."""
        self.ensure_one()
        order = self.sudo()
        todo = self.env.ref('mail.mail_activity_data_todo', raise_if_not_found=False)
        summary = self.env._("Doublon client à fusionner")
        if not todo or order.activity_ids.filtered(lambda a: a.summary == summary):
            return
        user = order.user_id or order.website_id.salesperson_id or self.env.ref('base.user_admin')
        lines = Markup('').join(
            Markup('<li>#%s %s &lt;%s&gt;</li>') % (p.id, p.name, p.email or '')
            for p in others)
        note = Markup(
            "<p>L'acheteur #%s %s &lt;%s&gt; a d'autres fiches :</p><ul>%s</ul>"
            "<p>Étiquettes déjà reportées. Fusionner pour réunir l'historique "
            "et l'espace client (Contacts &gt; Action &gt; Fusionner).</p>"
        ) % (order.partner_id.id, order.partner_id.name, order.partner_id.email or '', lines)
        order.activity_schedule(
            act_type_xmlid='mail.mail_activity_data_todo',
            summary=summary, note=note, user_id=user.id)

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
            docs = order.order_line.product_id.mapped(
                'product_tmpl_id.product_document_ids'
            ).filtered(lambda d: d.attached_on_sale == 'sale_order')
            if not docs:
                continue
            if not order.partner_id.email:
                continue
            # Les PDF sont des attachments privés (res_model=product.template) :
            # sans access_token, les liens /web/content du mail renvoient 404 pour
            # l'acheteur (anonyme ou portail). On garantit les tokens avant rendu.
            docs.ir_attachment_id.sudo().generate_access_token()
            order.sudo()._portal_ensure_token()
            access = order._ensure_ebook_portal_access()
            # force_send=True : livraison transactionnelle immédiate à la confirmation,
            # sans passer par la file (sinon coincée derrière un éventuel mass-mailing).
            template.with_context(**access).send_mail(order.id, force_send=True)
            order.ebook_delivery_sent = True

    def _ensure_ebook_portal_access(self):
        """Crée en silence le compte portail de l'acheteur, pour que l'espace
        client annoncé par l'email de livraison existe vraiment.

        Le paiement se fait sans compte obligatoire : sans ce compte, « Mot de
        passe oublié » ne trouve personne et l'acheteur se croit effacé.

        Retourne le contexte de rendu de l'email :
        - ebook_signup_url : lien « choisir mon mot de passe » (compte créé ici) ;
        - ebook_has_account : le contact avait déjà son compte.
        Rien si l'adresse sert déjà d'identifiant à un AUTRE contact (doublon né
        au paiement) : ce compte-là ne verrait pas la commande, l'email ne promet
        donc rien de plus que le lien avec jeton.

        sudo : la confirmation se fait en public (paiement web) ou par un vendeur
        sans droits sur res.users. Jamais bloquant : un échec ne doit pas empêcher
        la livraison."""
        self.ensure_one()
        partner = self.partner_id.sudo()
        if partner.with_context(active_test=False).user_ids:
            return {'ebook_has_account': True}
        email = email_normalize(partner.email or '')
        if not email:
            return {}
        Users = self.env['res.users'].sudo().with_context(active_test=False)
        if Users.search_count([('login', '=ilike', email)]):
            return {}
        company = self.company_id or self.env.company
        try:
            with self.env.cr.savepoint():
                Users.with_context(no_reset_password=True)._create_user_from_template({
                    'email': email,
                    'login': email,
                    'partner_id': partner.id,
                    'company_id': company.id,
                    'company_ids': [(6, 0, company.ids)],
                })
                partner.signup_prepare()
                signup_url = partner._get_signup_url()
        except Exception:
            _logger.exception(
                'ebook lifecycle: compte client non créé pour le partner %s', partner.id)
            return {}
        return {'ebook_signup_url': signup_url}

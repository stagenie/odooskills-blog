import re
from datetime import timedelta

from odoo import api, fields, models

_EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')


class OskiLeadCapture(models.AbstractModel):
    _name = 'oski.lead.capture'
    _description = "Logique de capture d'un lead (email)"

    @api.model
    def _disposable_domains(self):
        raw = self.env['ir.config_parameter'].sudo().get_param(
            'oski_lead_magnet.disposable_domains', '')
        return {d.strip().lower() for d in raw.split(',') if d.strip()}

    @api.model
    def _prospects_list(self):
        ML = self.env['mailing.list'].sudo()
        lst = ML.search([('name', '=', 'Prospects OdooSkills')], limit=1)
        if not lst:
            lst = ML.create({'name': 'Prospects OdooSkills'})
        return lst

    @api.model
    def _source_category(self, source):
        name = 'Lead PDF' if (source or '').startswith('pdf') else 'Lead popup'
        Cat = self.env['res.partner.category'].sudo()
        cat = Cat.search([('name', '=', name)], limit=1)
        return cat or Cat.create({'name': name})

    @api.model
    def _oski_capture_lead(self, email, consent, source, blog_post=None, client_ip=None):
        if client_ip:
            Attempt = self.env['oski.lead.attempt'].sudo()
            window = fields.Datetime.now() - timedelta(seconds=60)
            try:
                limit = int(self.env['ir.config_parameter'].sudo().get_param(
                    'oski_lead_magnet.rate_limit_per_min', '10'))
            except (TypeError, ValueError):
                limit = 10
            if Attempt.search_count([('ip', '=', client_ip), ('create_date', '>=', window)]) >= limit:
                return {'ok': False, 'error': 'rate_limited', 'pdf_url': None, 'new': False}
            Attempt.create({'ip': client_ip})

        email = (email or '').strip().lower()
        if not _EMAIL_RE.match(email):
            return {'ok': False, 'error': 'invalid', 'pdf_url': None, 'new': False}
        if email.split('@')[-1] in self._disposable_domains():
            return {'ok': False, 'error': 'disposable', 'pdf_url': None, 'new': False}

        # Anti-doublon concurrent : deux POST simultanés du même email
        # (double-clic sur le popup) racaient le search-then-create ci-dessous
        # et créaient deux fois le partner ET le mailing.contact. Ce verrou
        # transactionnel PG (relâché au COMMIT, propre à cet email) sérialise
        # les deux : le second voit l'enregistrement du premier et le réutilise.
        self.env.cr.execute("SELECT pg_advisory_xact_lock(hashtext(%s))", (email,))

        Partner = self.env['res.partner'].sudo()
        partner = Partner.search([('email', '=ilike', email)], limit=1)
        if not partner:
            partner = Partner.create({'name': email, 'email': email})
        partner.category_id = [(4, self._source_category(source).id)]

        if consent:
            lst = self._prospects_list()
            MC = self.env['mailing.contact'].sudo()
            contact = MC.search([('email', '=ilike', email)], limit=1)
            if not contact:
                contact = MC.create({'name': partner.name, 'email': email})
            if lst not in contact.list_ids:
                contact.list_ids = [(4, lst.id)]

        # RGPD : la relance promo est du marketing (mail welcome offer) ; on ne
        # la déclenche que si l'internaute a coché le consentement. Sans
        # consentement : partner/tag/PDF quand même, mais pas d'offre.
        Offer = self.env['oski.welcome.offer'].sudo()
        is_new = False
        if consent and Offer._offer_active():
            already = Offer.search_count([('email', '=', email)])
            has_bought = bool(self.env['sale.order'].sudo().search_count(
                [('partner_id', '=', partner.id), ('state', '=', 'sale')]))
            is_new = not already and not has_bought
            if is_new:
                Offer.create_for_email(email, partner, source)

        pdf_url = blog_post._oski_pdf_gated_url() if blog_post else None
        return {
            'ok': True, 'error': None, 'pdf_url': pdf_url or None, 'new': is_new,
            'subscribed': self._oski_is_subscribed(email),
        }

    @api.model
    def _oski_is_subscribed(self, email):
        """L'adresse est-elle déjà dans la liste Prospects ?

        Sert à ne pas redemander son accord à quelqu'un qui l'a déjà donné.
        """
        email = (email or '').strip().lower()
        if not _EMAIL_RE.match(email):
            return False
        contact = self.env['mailing.contact'].sudo().search(
            [('email', '=ilike', email)], limit=1)
        return bool(contact and self._prospects_list() in contact.list_ids)

    @api.model
    def _oski_grant_consent(self, email):
        """Enregistre un consentement donné APRÈS le téléchargement.

        L'écran de confirmation propose l'inscription une fois le PDF obtenu :
        le clic sur le bouton est un acte positif explicite, donc un
        consentement valide (RGPD art. 4-11) — contrairement à une case
        pré-cochée, cf. CJUE Planet49 C-673/17.

        L'offre de bienvenue n'est PAS déclenchée ici : depuis le revert du
        19/07 la remise est découplée de l'inscription et pilotée par
        campagne email. Ce point d'entrée ne fait qu'inscrire à la liste.
        """
        email = (email or '').strip().lower()
        if not _EMAIL_RE.match(email):
            return False
        # Même garde anti-doublon concurrent que _oski_capture_lead.
        self.env.cr.execute("SELECT pg_advisory_xact_lock(hashtext(%s))", (email,))
        partner = self.env['res.partner'].sudo().search(
            [('email', '=ilike', email)], limit=1)
        MC = self.env['mailing.contact'].sudo()
        contact = MC.search([('email', '=ilike', email)], limit=1)
        if not contact:
            contact = MC.create({'name': partner.name if partner else email,
                                 'email': email})
        lst = self._prospects_list()
        if lst not in contact.list_ids:
            contact.list_ids = [(4, lst.id)]
        return True

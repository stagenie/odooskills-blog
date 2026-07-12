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
            limit = int(self.env['ir.config_parameter'].sudo().get_param(
                'oski_lead_magnet.rate_limit_per_min', '10'))
            if Attempt.search_count([('ip', '=', client_ip), ('create_date', '>=', window)]) >= limit:
                return {'ok': False, 'error': 'rate_limited', 'pdf_url': None, 'new': False}
            Attempt.create({'ip': client_ip})

        email = (email or '').strip().lower()
        if not _EMAIL_RE.match(email):
            return {'ok': False, 'error': 'invalid', 'pdf_url': None, 'new': False}
        if email.split('@')[-1] in self._disposable_domains():
            return {'ok': False, 'error': 'disposable', 'pdf_url': None, 'new': False}

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

        # RGPD : la relance -50% est du marketing (mail welcome offer) ; on ne
        # la déclenche que si l'internaute a coché le consentement. Sans
        # consentement : partner/tag/PDF quand même, mais pas d'offre.
        Offer = self.env['oski.welcome.offer'].sudo()
        is_new = False
        if consent:
            already = Offer.search_count([('email', '=', email)])
            has_bought = bool(self.env['sale.order'].sudo().search_count(
                [('partner_id', '=', partner.id), ('state', '=', 'sale')]))
            is_new = not already and not has_bought
            if is_new:
                Offer.create_for_email(email, partner, source)

        pdf_url = blog_post._oski_pdf_gated_url() if blog_post else None
        return {'ok': True, 'error': None, 'pdf_url': pdf_url or None, 'new': is_new}

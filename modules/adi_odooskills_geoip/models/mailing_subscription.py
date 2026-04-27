from odoo import api, models
from odoo.http import request

from .mailing_contact import CONSENT_TEXT_VERSION


class MailingSubscription(models.Model):
    _inherit = 'mailing.subscription'

    @api.model_create_multi
    def create(self, vals_list):
        subs = super().create(vals_list)
        Contact = self.env['mailing.contact']
        ip = Contact._extract_request_ip()
        if not ip and not request:
            return subs
        country_id = None
        for sub in subs:
            contact = sub.contact_id
            if not contact:
                continue
            if ip and not contact.signup_ip:
                contact.signup_ip = ip
            if request and not contact.consent_text_version:
                contact.consent_text_version = CONSENT_TEXT_VERSION
            if contact.country_id or not ip:
                continue
            if country_id is None:
                country_id = Contact._geoip_country(ip)
            if country_id:
                contact.country_id = country_id
        return subs

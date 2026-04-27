from odoo import api, models


class MailingSubscription(models.Model):
    _inherit = 'mailing.subscription'

    @api.model_create_multi
    def create(self, vals_list):
        subs = super().create(vals_list)
        Contact = self.env['mailing.contact']
        ip = Contact._extract_request_ip()
        if not ip:
            return subs
        country_id = None
        for sub in subs:
            contact = sub.contact_id
            if not contact:
                continue
            if not contact.signup_ip:
                contact.signup_ip = ip
            if contact.country_id:
                continue
            if country_id is None:
                country_id = Contact._geoip_country(ip)
            if country_id:
                contact.country_id = country_id
        return subs

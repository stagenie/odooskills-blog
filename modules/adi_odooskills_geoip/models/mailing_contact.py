import json
import logging
import urllib.request
from urllib.parse import quote

from odoo import api, fields, models
from odoo.http import request

_logger = logging.getLogger(__name__)

_PRIVATE_PREFIXES = (
    '10.', '127.', '169.254.', '192.168.',
    '172.16.', '172.17.', '172.18.', '172.19.',
    '172.20.', '172.21.', '172.22.', '172.23.',
    '172.24.', '172.25.', '172.26.', '172.27.',
    '172.28.', '172.29.', '172.30.', '172.31.',
    '::1', 'fc00:', 'fd00:', 'fe80:',
)
_GEOIP_URL = 'http://ip-api.com/json/{ip}?fields=status,countryCode'
_GEOIP_TIMEOUT = 3


class MailingContact(models.Model):
    _inherit = 'mailing.contact'

    signup_ip = fields.Char(string='Signup IP', readonly=True, copy=False)

    @api.model_create_multi
    def create(self, vals_list):
        ip = self._extract_request_ip()
        if ip:
            for vals in vals_list:
                vals.setdefault('signup_ip', ip)
        contacts = super().create(vals_list)
        if ip:
            country_id = self._geoip_country(ip)
            if country_id:
                to_set = contacts.filtered(lambda c: not c.country_id)
                if to_set:
                    to_set.write({'country_id': country_id})
        return contacts

    @staticmethod
    def _extract_request_ip():
        if not request:
            return None
        env_http = request.httprequest.environ
        fwd = env_http.get('HTTP_X_FORWARDED_FOR')
        if fwd:
            return fwd.split(',')[0].strip()
        return env_http.get('REMOTE_ADDR')

    def _geoip_country(self, ip):
        if not ip or any(ip.startswith(p) for p in _PRIVATE_PREFIXES):
            return False
        try:
            req = urllib.request.Request(
                _GEOIP_URL.format(ip=quote(ip)),
                headers={'User-Agent': 'OdooSkills/1.0'},
            )
            with urllib.request.urlopen(req, timeout=_GEOIP_TIMEOUT) as resp:
                data = json.loads(resp.read().decode('utf-8'))
        except Exception as e:
            _logger.warning("GeoIP lookup failed for %s: %s", ip, e)
            return False
        if data.get('status') != 'success':
            return False
        code = (data.get('countryCode') or '').upper()
        if not code:
            return False
        country = self.env['res.country'].search([('code', '=', code)], limit=1)
        return country.id if country else False

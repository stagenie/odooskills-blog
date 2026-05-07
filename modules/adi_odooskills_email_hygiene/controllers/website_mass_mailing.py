import logging

from odoo import http
from odoo.http import request
from odoo.addons.website_mass_mailing.controllers.main import MassMailController

from ..models.email_validator import _redact_email

_logger = logging.getLogger(__name__)

REJECT_MESSAGES_FR = {
    'syntax_ko': "L'adresse email saisie n'est pas valide.",
    'role_based': "Merci d'utiliser une adresse personnelle (ex. prenom@…).",
    'disposable': "Les adresses email temporaires ne sont pas acceptées.",
    'mx_ko': "Le domaine de cette adresse n'accepte pas les emails.",
    'dns_timeout': "La vérification a échoué, merci de réessayer dans quelques instants.",
}


class MassMailControllerHygiene(MassMailController):

    @http.route()
    def subscribe(self, list_id, value, subscription_type, **post):
        # Only validate emails — mobile subscriptions go through native logic
        if subscription_type == 'email':
            validator = request.env['email.validator'].sudo()
            status, _reason = validator.validate(value)
            if status != 'valid':
                ua = request.httprequest.user_agent.string or ''
                _logger.info(
                    "email_hygiene reject email=%s reason=%s remote_ip=%s ua=%s",
                    _redact_email(value),
                    status,
                    request.httprequest.remote_addr,
                    ua[:200],
                )
                return {
                    'toast_type': 'danger',
                    'toast_content': REJECT_MESSAGES_FR.get(
                        status, REJECT_MESSAGES_FR['syntax_ko']
                    ),
                }
        return super().subscribe(list_id, value, subscription_type, **post)

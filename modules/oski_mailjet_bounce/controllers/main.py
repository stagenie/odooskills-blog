import json
import logging

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

# Événements Mailjet qui justifient un blacklist définitif de l'adresse.
_BLACKLIST_EVENTS = ('blocked', 'spam', 'unsub')


class MailjetWebhook(http.Controller):
    """Reçoit les événements Mailjet (Event API) et blackliste les adresses mortes.

    Mailjet ne signe pas ses payloads : l'authentification repose sur le token
    secret présent dans l'URL (paramètre système ``oski.mailjet_webhook_token``).
    Le payload est soit un objet JSON unique, soit un tableau (grouping activé).
    """

    @http.route('/mailjet/events/<string:token>', type='http', auth='public',
                methods=['POST'], csrf=False, save_session=False)
    def mailjet_events(self, token, **kwargs):
        expected = request.env['ir.config_parameter'].sudo().get_param('oski.mailjet_webhook_token')
        if not expected or token != expected:
            _logger.warning("Webhook Mailjet : token invalide")
            return request.make_response('forbidden', status=403)

        try:
            raw = request.httprequest.get_data(as_text=True) or '[]'
            data = json.loads(raw)
        except (ValueError, TypeError):
            _logger.warning("Webhook Mailjet : payload JSON invalide")
            return request.make_response('bad request', status=400)

        events = data if isinstance(data, list) else [data]
        blacklist = request.env['mail.blacklist'].sudo()
        added = 0
        for ev in events:
            if not isinstance(ev, dict):
                continue
            etype = (ev.get('event') or '').lower()
            email = ev.get('email')
            if not email:
                continue
            should_blacklist = (
                etype in _BLACKLIST_EVENTS
                or (etype == 'bounce' and (ev.get('hard_bounce') or ev.get('blocked')))
            )
            if not should_blacklist:
                continue
            reason = ev.get('error') or ev.get('error_related_to') or ''
            message = "Blacklisté automatiquement — Mailjet event=%s %s" % (etype, reason)
            try:
                blacklist._add(email, message=message)
                added += 1
            except Exception:  # ne jamais faire échouer le webhook (Mailjet retenterait)
                _logger.exception("Webhook Mailjet : échec blacklist de %s", email)

        _logger.info("Webhook Mailjet : %s événements reçus, %s adresses blacklistées", len(events), added)
        return request.make_response('OK', status=200)

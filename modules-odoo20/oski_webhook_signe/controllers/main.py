import hashlib
import hmac
import json
import time

from odoo import http
from odoo.http import request

MAX_AGE = 300  # secondes : au-delà, une requête signée est refusée (rejeu)


class SignatureWebhook(http.Controller):

    @http.route('/oski/webhook/signature', type='http', auth='public', methods=['POST'],
                csrf=False, save_session=False)
    def signature_received(self):
        body = request.httprequest.get_data()
        timestamp = request.httprequest.headers.get('X-Timestamp', '')
        received = request.httprequest.headers.get('X-Signature', '')
        secret = request.env['ir.config_parameter'].sudo().get_str('oski_webhook_signe.secret')

        # 1. Authentifier : HMAC-SHA256 de « horodatage.corps » avec le secret partagé
        expected = hmac.new(secret.encode(), f"{timestamp}.".encode() + body, hashlib.sha256).hexdigest()
        if not secret or not hmac.compare_digest(received.encode(), expected.encode()):
            return request.make_json_response({'status': 'error', 'error': 'signature'}, status=401)
        if not timestamp.isdigit() or abs(time.time() - int(timestamp)) > MAX_AGE:
            return request.make_json_response({'status': 'error', 'error': 'expired'}, status=401)

        # 2. Lire le corps
        try:
            data = json.loads(body)
        except ValueError:
            data = None
        if not isinstance(data, dict):
            return request.make_json_response({'status': 'error', 'error': 'json'}, status=400)

        # 3. Agir avec les droits d'un utilisateur dédié, pas en superutilisateur
        request.update_env(user=request.env.ref('oski_webhook_signe.user_webhook'))
        order = request.env['sale.order'].search([('name', '=', data.get('commande'))], limit=1)
        if not order:
            return request.make_json_response({'status': 'error', 'error': 'commande'}, status=404)
        order.message_post(body=request.env._("Devis signé en ligne par %s.", data.get('signataire')))
        if order.state in ('draft', 'sent'):
            order.action_confirm()
        return request.make_json_response({'status': 'ok', 'commande': order.name, 'etat': order.state})

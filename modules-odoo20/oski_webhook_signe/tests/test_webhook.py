import hashlib
import hmac
import json
import time

from odoo.tests import HttpCase, tagged

SECRET = "secret-de-test"
URL = "/oski/webhook/signature"


@tagged('post_install', '-at_install')
class TestSignatureWebhook(HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env['ir.config_parameter'].set_str('oski_webhook_signe.secret', SECRET)
        partner = cls.env['res.partner'].create({'name': "Client webhook"})
        product = cls.env['product.product'].create({'name': "Article webhook", 'list_price': 10})
        cls.order = cls.env['sale.order'].create({
            'partner_id': partner.id,
            'order_line': [(0, 0, {'product_id': product.id, 'product_uom_qty': 1})],
        })

    def _post(self, payload, secret=SECRET, timestamp=None):
        body = json.dumps(payload).encode()
        timestamp = str(int(time.time()) if timestamp is None else timestamp)
        signature = hmac.new(secret.encode(), f"{timestamp}.".encode() + body, hashlib.sha256).hexdigest()
        return self.url_open(URL, data=body, headers={
            'Content-Type': 'application/json', 'X-Timestamp': timestamp, 'X-Signature': signature,
        })

    def test_valid_signature_confirms_order(self):
        response = self._post({'commande': self.order.name, 'signataire': "Jeanne Test"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['etat'], 'sale')
        self.assertEqual(self.order.state, 'sale')
        message = self.order.message_ids.filtered(lambda m: "Jeanne Test" in str(m.body))
        self.assertEqual(message.author_id, self.env.ref('oski_webhook_signe.user_webhook').partner_id)

    def test_wrong_secret_is_refused(self):
        response = self._post({'commande': self.order.name}, secret="mauvais")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(self.order.state, 'draft')

    def test_old_request_is_refused(self):
        response = self._post({'commande': self.order.name}, timestamp=int(time.time()) - 3600)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['error'], 'expired')

    def test_unknown_order(self):
        response = self._post({'commande': "S99999"})
        self.assertEqual(response.status_code, 404)

    def test_body_must_be_an_object(self):
        response = self._post(["S00001"])
        self.assertEqual(response.status_code, 400)

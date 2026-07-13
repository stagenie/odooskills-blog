import json

from odoo.tests import HttpCase, tagged


@tagged('post_install', '-at_install')
class TestGridRoute(HttpCase):
    def test_grid_route_returns_percent_and_rows(self):
        self.env['ir.config_parameter'].sudo().set_param(
            'oski_lead_magnet.welcome_percent', '30')
        resp = self.url_open(
            '/oski/offer/grid',
            data=json.dumps({'jsonrpc': '2.0', 'method': 'call', 'params': {}}),
            headers={'Content-Type': 'application/json'})
        self.assertEqual(resp.status_code, 200)
        result = resp.json()['result']
        self.assertEqual(result['percent'], 30)
        self.assertIsInstance(result['rows'], list)

from odoo.tests import HttpCase, tagged


@tagged('post_install', '-at_install')
class TestWording(HttpCase):
    def test_popup_shows_current_percent(self):
        self.env['ir.config_parameter'].sudo().set_param(
            'oski_lead_magnet.welcome_percent', '30')
        html = self.url_open('/').text
        self.assertIn('-30%', html)
        self.assertNotIn('-50%', html)

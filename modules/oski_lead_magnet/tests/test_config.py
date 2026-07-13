from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestConfig(TransactionCase):
    def test_program_exists(self):
        prog = self.env.ref('oski_lead_magnet.welcome_program')
        self.assertEqual(prog.program_type, 'coupons')
        reward = prog.reward_ids[:1]
        self.assertEqual(reward.discount, 30.0)
        self.assertEqual(reward.discount_mode, 'percent')
        self.assertEqual(reward.discount_applicability, 'specific')
        self.assertTrue(reward.discount_product_domain and reward.discount_product_domain != '[]')

    def test_params(self):
        ICP = self.env['ir.config_parameter'].sudo()
        self.assertEqual(ICP.get_param('oski_lead_magnet.offer_hours'), '72')
        self.assertTrue(ICP.get_param('oski_lead_magnet.disposable_domains'))

    def test_welcome_percent_default_30(self):
        reward = self.env.ref('oski_lead_magnet.welcome_reward')
        self.assertEqual(reward.discount, 30.0)
        val = self.env['ir.config_parameter'].sudo().get_param('oski_lead_magnet.welcome_percent')
        self.assertEqual(int(val), 30)

    def test_settings_sync_reward(self):
        settings = self.env['res.config.settings'].create({'oski_welcome_percent': 40})
        settings.set_values()
        self.assertEqual(self.env.ref('oski_lead_magnet.welcome_reward').discount, 40.0)
        self.assertEqual(
            int(self.env['ir.config_parameter'].sudo().get_param('oski_lead_magnet.welcome_percent')),
            40)

    def test_settings_out_of_range_percent_clamped(self):
        settings = self.env['res.config.settings'].create({'oski_welcome_percent': 95})
        settings.set_values()
        # display helper and real reward must agree, both clamped to 30
        self.assertEqual(self.env['oski.welcome.offer']._welcome_percent(), 30)
        self.assertEqual(self.env.ref('oski_lead_magnet.welcome_reward').discount, 30.0)
        self.assertEqual(
            int(self.env['ir.config_parameter'].sudo().get_param('oski_lead_magnet.welcome_percent')),
            30)

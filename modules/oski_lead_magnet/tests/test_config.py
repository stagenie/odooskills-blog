from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestConfig(TransactionCase):
    def test_program_exists(self):
        prog = self.env.ref('oski_lead_magnet.welcome_program')
        self.assertEqual(prog.program_type, 'coupons')
        reward = prog.reward_ids[:1]
        self.assertEqual(reward.discount, 50.0)
        self.assertEqual(reward.discount_mode, 'percent')
        self.assertEqual(reward.discount_applicability, 'specific')
        self.assertTrue(reward.discount_product_domain and reward.discount_product_domain != '[]')

    def test_params(self):
        ICP = self.env['ir.config_parameter'].sudo()
        self.assertEqual(ICP.get_param('oski_lead_magnet.offer_hours'), '72')
        self.assertTrue(ICP.get_param('oski_lead_magnet.disposable_domains'))

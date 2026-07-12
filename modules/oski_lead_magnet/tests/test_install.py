from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestInstall(TransactionCase):
    def test_module_installed(self):
        mod = self.env['ir.module.module'].search([('name', '=', 'oski_lead_magnet')])
        self.assertEqual(mod.state, 'installed')

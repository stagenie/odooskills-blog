from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestInstall(TransactionCase):
    def test_module_installed(self):
        module = self.env['ir.module.module'].search(
            [('name', '=', 'oski_article_pdf')], limit=1)
        self.assertTrue(module, "le module doit exister au registre")
        self.assertEqual(module.state, 'installed')

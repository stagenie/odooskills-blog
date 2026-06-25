from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestXlsxExport(TransactionCase):

    def test_xlsx_bytes_are_valid(self):
        partner = self.env['res.partner'].create({'name': 'Client Démo'})
        product = self.env['product.product'].create({
            'name': 'Produit Démo', 'list_price': 100.0,
        })
        order = self.env['sale.order'].create({
            'partner_id': partner.id,
            'order_line': [(0, 0, {
                'product_id': product.id, 'product_uom_qty': 3,
            })],
        })
        data = order._build_sale_lines_xlsx()
        # Un .xlsx est une archive zip → signature magique "PK".
        self.assertEqual(data[:2], b'PK', "Le binaire produit doit être un fichier XLSX (zip)")
        self.assertGreater(len(data), 100)

    def test_action_returns_act_url(self):
        partner = self.env['res.partner'].create({'name': 'Client Démo 2'})
        order = self.env['sale.order'].create({'partner_id': partner.id})
        action = order.action_export_lines_xlsx()
        self.assertEqual(action['type'], 'ir.actions.act_url')
        self.assertIn('/odooskills/export/sale_lines/xlsx', action['url'])
        self.assertIn(str(order.id), action['url'])

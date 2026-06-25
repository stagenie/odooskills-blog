import io
import zipfile

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestXlsxBulkExport(TransactionCase):

    def _confirmed_orders(self):
        partner = self.env['res.partner'].create({'name': 'Client Démo'})
        p1 = self.env['product.product'].create({'name': 'Produit A', 'list_price': 100.0})
        p2 = self.env['product.product'].create({'name': 'Produit B', 'list_price': 50.0})
        orders = self.env['sale.order']
        for qty1, qty2 in ((3, 1), (2, 4)):
            o = self.env['sale.order'].create({
                'partner_id': partner.id, 'date_order': '2026-03-10 09:00:00',
                'order_line': [
                    (0, 0, {'product_id': p1.id, 'product_uom_qty': qty1}),
                    (0, 0, {'product_id': p2.id, 'product_uom_qty': qty2}),
                ],
            })
            o.action_confirm()
            orders |= o
        return orders

    def test_xlsx_valid_and_two_sheets(self):
        self._confirmed_orders()
        data = self.env['sale.order']._build_sales_xlsx_bulk()
        self.assertEqual(data[:2], b'PK', "Le binaire produit doit être un fichier XLSX (zip)")
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            workbook_xml = zf.read('xl/workbook.xml').decode()
        self.assertEqual(workbook_xml.count('<sheet '), 2, "Deux feuilles de synthèse attendues")
        self.assertIn('produit', workbook_xml)
        self.assertIn('mensuelle', workbook_xml)

    def test_summary_data_matches_sql_aggregation(self):
        self._confirmed_orders()
        products, months = self.env['sale.order']._bulk_summary_data()
        # Recoupement indépendant : somme directe via _read_group.
        line_domain = [('display_type', '=', False),
                       ('order_id.state', 'in', ('sale', 'done'))]
        groups = dict(
            (p.display_name, s) for p, s in
            self.env['sale.order.line']._read_group(
                line_domain, ['product_id'], ['price_subtotal:sum'])
        )
        for name, count, amount in products:
            self.assertAlmostEqual(amount, groups[name], places=2)
        # Tri décroissant sur le CA.
        amounts = [r[2] for r in products]
        self.assertEqual(amounts, sorted(amounts, reverse=True))
        # Au moins un mois agrégé, libellé 'MM/AAAA'.
        self.assertTrue(months)
        self.assertRegex(months[0][0], r'^\d{2}/\d{4}$')

    def test_action_returns_act_url(self):
        action = self.env['sale.order'].action_export_sales_xlsx_bulk()
        self.assertEqual(action['type'], 'ir.actions.act_url')
        self.assertEqual(action['url'], '/odooskills/export/sales/xlsx_bulk')

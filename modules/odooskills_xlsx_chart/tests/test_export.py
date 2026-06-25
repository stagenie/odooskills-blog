import io
import zipfile

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestXlsxChartExport(TransactionCase):

    def _orders(self):
        partner = self.env['res.partner'].create({'name': 'Client Démo'})
        p1 = self.env['product.product'].create({'name': 'Produit A', 'list_price': 100.0})
        p2 = self.env['product.product'].create({'name': 'Produit B', 'list_price': 50.0})
        o1 = self.env['sale.order'].create({
            'partner_id': partner.id, 'date_order': '2026-01-15 10:00:00',
            'order_line': [
                (0, 0, {'product_id': p1.id, 'product_uom_qty': 3}),
                (0, 0, {'product_id': p2.id, 'product_uom_qty': 1}),
            ],
        })
        o2 = self.env['sale.order'].create({
            'partner_id': partner.id, 'date_order': '2026-02-10 10:00:00',
            'order_line': [(0, 0, {'product_id': p1.id, 'product_uom_qty': 2})],
        })
        return o1 | o2

    def test_xlsx_bytes_are_valid(self):
        data = self._orders()._build_sale_lines_xlsx_chart()
        self.assertEqual(data[:2], b'PK', "Le binaire produit doit être un fichier XLSX (zip)")
        self.assertGreater(len(data), 100)

    def test_three_charts_embedded(self):
        data = self._orders()._build_sale_lines_xlsx_chart()
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            charts = [n for n in zf.namelist()
                      if n.startswith('xl/charts/chart') and n.endswith('.xml')]
        self.assertEqual(len(charts), 3, "Trois graphiques attendus (histogramme, camembert, courbe)")

    def test_chart_types_present(self):
        data = self._orders()._build_sale_lines_xlsx_chart()
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            blob = '\n'.join(
                zf.read(n).decode()
                for n in zf.namelist()
                if n.startswith('xl/charts/chart') and n.endswith('.xml')
            )
        # xlsxwriter écrit les types natifs Excel : barChart (colonne),
        # pieChart, lineChart.
        self.assertIn('barChart', blob, "Histogramme (column) attendu")
        self.assertIn('pieChart', blob, "Camembert (pie) attendu")
        self.assertIn('lineChart', blob, "Courbe (line) attendue")

    def test_aggregate_orders_products_desc_and_months_chrono(self):
        products, months = self._orders()._aggregate_ca()
        # Produit A (5 unités) > Produit B (1) → A en tête.
        self.assertEqual(products[0][0], 'Produit A')
        self.assertGreater(products[0][1], products[1][1])
        # Deux mois, ordre chronologique avec libellé 'MM/AAAA'.
        self.assertEqual([m[0] for m in months], ['01/2026', '02/2026'])

    def test_action_returns_act_url(self):
        order = self._orders()[0]
        action = order.action_export_lines_xlsx_chart()
        self.assertEqual(action['type'], 'ir.actions.act_url')
        self.assertIn('/odooskills/export/sale_lines/xlsx_chart', action['url'])
        self.assertIn(str(order.id), action['url'])

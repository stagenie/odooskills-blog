import io
import zipfile

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestXlsxFormatExport(TransactionCase):

    def _make_order(self):
        partner = self.env['res.partner'].create({'name': 'Client Démo'})
        product = self.env['product.product'].create({
            'name': 'Produit Démo', 'list_price': 100.0,
        })
        return self.env['sale.order'].create({
            'partner_id': partner.id,
            'order_line': [(0, 0, {
                'product_id': product.id, 'product_uom_qty': 3, 'discount': 10.0,
            })],
        })

    def test_xlsx_bytes_are_valid(self):
        data = self._make_order()._build_sale_lines_xlsx_pro()
        # Un .xlsx est une archive zip → signature magique "PK".
        self.assertEqual(data[:2], b'PK', "Le binaire produit doit être un fichier XLSX (zip)")
        self.assertGreater(len(data), 100)

    def test_workbook_carries_advanced_formatting(self):
        data = self._make_order()._build_sale_lines_xlsx_pro()
        # Inspecter le XML interne du classeur : la mise en forme avancée
        # laisse des traces vérifiables (cellule fusionnée, volets figés,
        # formatage conditionnel).
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            sheet_xml = zf.read('xl/worksheets/sheet1.xml').decode()
        self.assertIn('<mergeCells', sheet_xml, "Le titre doit être fusionné (merge_range)")
        self.assertIn('<pane', sheet_xml, "Les volets doivent être figés (freeze_panes)")
        self.assertIn('conditionalFormatting', sheet_xml, "Dégradé conditionnel attendu")

    def test_action_returns_act_url(self):
        order = self._make_order()
        action = order.action_export_lines_xlsx_pro()
        self.assertEqual(action['type'], 'ir.actions.act_url')
        self.assertIn('/odooskills/export/sale_lines/xlsx_pro', action['url'])
        self.assertIn(str(order.id), action['url'])

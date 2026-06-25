import io
import zipfile

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestXlsxSheetsExport(TransactionCase):

    def _make_order(self, salesperson, partner_name='Client Démo'):
        partner = self.env['res.partner'].create({'name': partner_name})
        product = self.env['product.product'].create({
            'name': 'Produit Démo', 'list_price': 100.0,
        })
        return self.env['sale.order'].create({
            'partner_id': partner.id,
            'user_id': salesperson.id,
            'order_line': [(0, 0, {'product_id': product.id, 'product_uom_qty': 2})],
        })

    def _two_salespeople_orders(self):
        alice = self.env['res.users'].create({
            'name': 'Alice Commercial', 'login': 'alice_xlsx_sheets',
        })
        bob = self.env['res.users'].create({
            'name': 'Bob Commercial', 'login': 'bob_xlsx_sheets',
        })
        return (self._make_order(alice, 'Client A')
                | self._make_order(alice, 'Client A2')
                | self._make_order(bob, 'Client B'))

    def test_xlsx_bytes_are_valid(self):
        data = self._two_salespeople_orders()._build_sale_lines_xlsx_sheets()
        self.assertEqual(data[:2], b'PK', "Le binaire produit doit être un fichier XLSX (zip)")
        self.assertGreater(len(data), 100)

    def test_workbook_has_one_sheet_per_salesperson_plus_summary(self):
        data = self._two_salespeople_orders()._build_sale_lines_xlsx_sheets()
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            workbook_xml = zf.read('xl/workbook.xml').decode()
        # 2 commerciaux → 2 feuilles de détail + 1 feuille Sommaire = 3.
        self.assertEqual(workbook_xml.count('<sheet '), 3, "3 feuilles attendues")
        self.assertIn('Sommaire', workbook_xml)
        self.assertIn('Alice Commercial', workbook_xml)
        self.assertIn('Bob Commercial', workbook_xml)

    def test_summary_carries_internal_hyperlinks(self):
        data = self._two_salespeople_orders()._build_sale_lines_xlsx_sheets()
        # xlsxwriter nomme les fichiers sheetN.xml dans l'ordre de création :
        # le sommaire est créé en dernier. On balaie donc toutes les feuilles.
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            all_xml = '\n'.join(
                zf.read(n).decode()
                for n in zf.namelist()
                if n.startswith('xl/worksheets/sheet') and n.endswith('.xml')
            )
        # Les liens internes (write_url internal:) produisent des <hyperlink>
        # avec un attribut `location`, et PAS de relation externe.
        self.assertIn('<hyperlink', all_xml, "Liens internes attendus dans le sommaire")
        self.assertIn('location=', all_xml)

    def test_sheet_name_sanitized_and_truncated(self):
        used = set()
        raw = "Commercial: Région [Nord]/Ouest très très très long nom"
        name = self.env['sale.order']._safe_sheet_name(raw, used)
        self.assertLessEqual(len(name), 31)
        for ch in '[]:*?/\\':
            self.assertNotIn(ch, name)
        # Collision → suffixe unique.
        name2 = self.env['sale.order']._safe_sheet_name(raw, used)
        self.assertNotEqual(name, name2)

    def test_action_returns_act_url(self):
        order = self._make_order(self.env.user)
        action = order.action_export_lines_xlsx_sheets()
        self.assertEqual(action['type'], 'ir.actions.act_url')
        self.assertIn('/odooskills/export/sale_lines/xlsx_sheets', action['url'])
        self.assertIn(str(order.id), action['url'])

import io
import zipfile
from datetime import date, timedelta

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestXlsxSchedule(TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({'name': 'Client Démo'})
        self.product = self.env['product.product'].create({
            'name': 'Produit Démo', 'list_price': 100.0,
        })

    def _confirmed_order(self, when):
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'date_order': fields.Datetime.to_datetime(when),
            'order_line': [(0, 0, {'product_id': self.product.id, 'product_uom_qty': 2})],
        })
        order.action_confirm()
        return order

    def test_build_orders_xlsx_valid(self):
        orders = self._confirmed_order(date.today())
        data = orders._build_orders_xlsx()
        self.assertEqual(data[:2], b'PK')
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            self.assertEqual(zf.read('xl/workbook.xml').decode().count('<sheet '), 1)

    def test_server_action_target_returns_download(self):
        orders = self._confirmed_order(date.today())
        action = orders.action_export_selected_xlsx()
        self.assertEqual(action['type'], 'ir.actions.act_url')
        self.assertIn('/web/content/', action['url'])
        self.assertIn('download=true', action['url'])

    def test_wizard_download_creates_attachment(self):
        self._confirmed_order(date.today())
        wizard = self.env['odooskills.sales.export.wizard'].create({
            'date_from': date.today().replace(day=1),
            'date_to': date.today(),
        })
        before = self.env['ir.attachment'].search_count([])
        action = wizard.action_download()
        after = self.env['ir.attachment'].search_count([])
        self.assertEqual(after, before + 1, "Une pièce jointe doit être créée")
        self.assertIn('/web/content/', action['url'])

    def test_wizard_rejects_inverted_dates(self):
        wizard = self.env['odooskills.sales.export.wizard'].create({
            'date_from': date.today(),
            'date_to': date.today() - timedelta(days=10),
        })
        with self.assertRaises(UserError):
            wizard.action_download()

    def test_cron_emails_when_recipient_configured(self):
        # Commande confirmée le mois dernier.
        first_this = date.today().replace(day=1)
        last_prev = first_this - timedelta(days=1)
        self._confirmed_order(last_prev)
        self.env['ir.config_parameter'].sudo().set_param(
            'odooskills.monthly_report_email', 'rapports@example.com')

        before = self.env['mail.mail'].search_count([])
        result = self.env['sale.order']._cron_email_monthly_report()
        self.assertTrue(result)
        mails = self.env['mail.mail'].search([], order='id desc', limit=1)
        self.assertEqual(self.env['mail.mail'].search_count([]), before + 1)
        self.assertEqual(mails.email_to, 'rapports@example.com')
        self.assertTrue(mails.attachment_ids, "L'e-mail doit porter une pièce jointe XLSX")

    def test_cron_skips_without_recipient(self):
        self.env.company.email = False
        self.env['ir.config_parameter'].sudo().set_param(
            'odooskills.monthly_report_email', '')
        result = self.env['sale.order']._cron_email_monthly_report()
        self.assertFalse(result)

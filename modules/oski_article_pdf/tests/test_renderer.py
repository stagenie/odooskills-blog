from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestRenderer(TransactionCase):
    def setUp(self):
        super().setUp()
        self.renderer = self.env['oski.pdf.renderer']
        self.env['ir.config_parameter'].sudo().set_param(
            'web.base.url', 'https://odooskills.com')

    def test_absolutize_img_src(self):
        html = '<img src="/web/image/42"/>'
        self.assertIn('https://odooskills.com/web/image/42',
                      self.renderer._absolutize(html))

    def test_absolutize_img_src_single_quotes(self):
        html = "<img src='/web/image/42'/>"
        result = self.renderer._absolutize(html)
        self.assertIn("src='https://odooskills.com/web/image/42'", result)

    def test_absolutize_leaves_protocol_relative_untouched(self):
        html = '<img src="//cdn.example/x.png"/>'
        self.assertEqual(self.renderer._absolutize(html), html)

    def test_absolutize_leaves_external_untouched(self):
        html = '<img src="https://ailleurs.example/x.png"/>'
        self.assertEqual(self.renderer._absolutize(html), html)

    def test_absolutize_ignores_anchors(self):
        html = '<a href="#section">x</a>'
        self.assertEqual(self.renderer._absolutize(html), html)

    def test_base_url_raises_when_unset(self):
        self.env['ir.config_parameter'].sudo().set_param('web.base.url', '')
        with self.assertRaises(UserError):
            self.renderer._base_url()

    def test_render_produces_pdf_bytes(self):
        pdf = self.renderer._render_pdf(
            '<html><body><h1>Bonjour</h1></body></html>')
        self.assertTrue(pdf.startswith(b'%PDF'), "doit commencer par %PDF")
        self.assertGreater(len(pdf), 500)

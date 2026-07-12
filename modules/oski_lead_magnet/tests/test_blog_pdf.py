import base64
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestBlogPdf(TransactionCase):
    def _att(self, name):
        return self.env['ir.attachment'].create({
            'name': name, 'datas': base64.b64encode(b'%PDF-1.4 test'),
            'mimetype': 'application/pdf',
        })

    def test_no_pdf_returns_false(self):
        post = self.env['blog.post'].create({'name': 'Sans PDF'})
        self.assertFalse(post._oski_pdf_download_url())

    def test_article_pdf_url(self):
        post = self.env['blog.post'].create({'name': 'Avec PDF'})
        post.oski_pdf_attachment_id = self._att('a.pdf')
        self.assertIn('/web/content/', post._oski_pdf_download_url())

    def test_series_pdf_takes_priority(self):
        series = self.env['oski.pdf.series'].create({
            'name': 'Série X', 'attachment_id': self._att('serie.pdf').id})
        post = self.env['blog.post'].create({'name': 'Article série'})
        post.oski_pdf_attachment_id = self._att('article.pdf')
        post.oski_pdf_series_id = series
        url = post._oski_pdf_download_url()
        self.assertIn(str(series.attachment_id.id), url)

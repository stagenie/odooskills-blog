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


@tagged('post_install', '-at_install')
class TestCoverUrl(TransactionCase):
    """Couverture d'article servant d'habillage au modal."""

    def _post(self, cover):
        blog = self.env['blog.blog'].create({'name': 'B'})
        return self.env['blog.post'].create({
            'name': 'A', 'blog_id': blog.id, 'cover_properties': cover})

    def test_cover_url_extraite(self):
        post = self._post('{"background-image": "url(\'/web/image/1-abc/x.png\')"}')
        self.assertEqual(post._oski_cover_url(), '/web/image/1-abc/x.png')

    def test_cover_id_simple_redimensionnee(self):
        """Le bandeau fait 92 px : inutile de servir l'original."""
        post = self._post('{"background-image": "url(/web/image/859)"}')
        self.assertEqual(post._oski_cover_url(), '/web/image/859/800x368')

    def test_cover_double_quotes(self):
        post = self._post('{"background-image": "url(\\"/web/image/9/y.jpg\\")"}')
        self.assertEqual(post._oski_cover_url(), '/web/image/9/y.jpg')

    def test_sans_cover(self):
        self.assertFalse(self._post('{"background-image": "none"}')._oski_cover_url())
        self.assertFalse(self._post('{}')._oski_cover_url())

    def test_json_casse_ne_leve_pas(self):
        self.assertFalse(self._post('pas du json')._oski_cover_url())

    def test_cover_externe_ignoree(self):
        """Le modal ne doit pas dépendre d'un hôte tiers pour s'afficher."""
        post = self._post('{"background-image": "url(https://ailleurs.example/x.png)"}')
        self.assertFalse(post._oski_cover_url())

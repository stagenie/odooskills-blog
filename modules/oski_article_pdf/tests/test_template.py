from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestTemplate(TransactionCase):
    def setUp(self):
        super().setUp()
        blog = self.env['blog.blog'].create({'name': 'Développement Odoo'})
        self.post = self.env['blog.post'].create({
            'name': 'Mon article', 'blog_id': blog.id,
            'content': '<p>Corps de test</p>', 'is_published': True})

    def _render(self, is_series=False):
        return self.env['ir.qweb']._render('oski_article_pdf.guide_document', {
            'posts': self.post, 'title': 'Mon article', 'subtitle': 'Sous-titre',
            'meta': 'Développement Odoo · 2026-07-19', 'is_series': is_series})

    def test_contains_cover_and_content(self):
        html = str(self._render())
        self.assertIn('Mon article', html)
        self.assertIn('Corps de test', html)
        self.assertIn('GUIDE PDF', html.upper())

    def test_no_toc_for_single_article(self):
        html = str(self._render(is_series=False))
        self.assertNotIn('<div class="osk-toc"', html)
        self.assertNotIn('Sommaire', html)

    def test_toc_present_for_series(self):
        html = str(self._render(is_series=True))
        self.assertIn('<div class="osk-toc"', html)
        self.assertIn('Sommaire', html)

    def test_never_says_ebook(self):
        self.assertNotIn('ebook', str(self._render()).lower())

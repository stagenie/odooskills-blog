from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestStale(TransactionCase):
    def setUp(self):
        super().setUp()
        blog = self.env['blog.blog'].create({'name': 'Blog test'})
        self.post = self.env['blog.post'].create({
            'name': 'Article test', 'blog_id': blog.id,
            'content': '<p>contenu initial</p>', 'is_published': True})

    def test_stale_when_never_generated(self):
        self.assertTrue(self.post.oski_pdf_stale)

    def test_not_stale_after_hash_recorded(self):
        self.post.oski_pdf_source_hash = self.post._oski_source_hash()
        self.post.oski_pdf_generated_on = '2026-07-19 10:00:00'
        self.assertFalse(self.post.oski_pdf_stale)

    def test_stale_after_content_change(self):
        self.post.oski_pdf_source_hash = self.post._oski_source_hash()
        self.post.oski_pdf_generated_on = '2026-07-19 10:00:00'
        self.post.content = '<p>contenu réécrit</p>'
        self.assertTrue(self.post.oski_pdf_stale)

    def test_title_change_also_makes_stale(self):
        self.post.oski_pdf_source_hash = self.post._oski_source_hash()
        self.post.oski_pdf_generated_on = '2026-07-19 10:00:00'
        self.post.name = 'Titre réécrit'
        self.assertTrue(self.post.oski_pdf_stale)

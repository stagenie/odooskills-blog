from odoo.tests import HttpCase, tagged

STORE = 'https://apps.odooskills.com/fr/apps?utm_source=odooskills'


@tagged('post_install', '-at_install')
class TestStoreCta(HttpCase):

    def test_store_cta_on_article_only(self):
        blog = self.env['blog.blog'].create({'name': 'Blog encart store'})
        post = self.env['blog.post'].create({
            'name': 'Article encart store', 'blog_id': blog.id,
            'content': '<p>Corps</p>', 'is_published': True})
        res = self.url_open(post.website_url)
        self.assertEqual(res.status_code, 200)
        page = res.text
        self.assertIn('Corps', page, page[:3000])
        self.assertEqual(page.count('o_oski_store_cta'), 1)
        self.assertIn(STORE, page.replace('&amp;', '&'))
        self.assertIn('target="_blank"', page[page.index('o_oski_store_cta'):])
        # l'encart suit le corps de l'article
        self.assertLess(page.index('Corps'), page.index('o_oski_store_cta'))
        listing = self.url_open('/blog/%s' % blog.id).text
        self.assertNotIn('o_oski_store_cta', listing)

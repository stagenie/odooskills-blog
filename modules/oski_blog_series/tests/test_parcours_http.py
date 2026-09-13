from datetime import datetime

from odoo.tests import HttpCase, tagged

PAST = datetime(2026, 4, 26, 6, 57)


@tagged('post_install', '-at_install')
class TestParcoursHttp(HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Series = cls.env['oski.blog.series']
        Post = cls.env['blog.post']
        cls.v19 = cls.env.ref('oski_blog_series.odoo_version_19')
        cls.v20 = cls.env.ref('oski_blog_series.odoo_version_20')
        cls.blog = cls.env['blog.blog'].create({'name': 'Blog parcours http'})
        cls.series = Series.create({
            'name': 'Serie publique dix-neuf', 'blog_id': cls.blog.id,
            'odoo_version_id': cls.v19.id, 'audience': 'Public visé test',
            'description': 'Description de la série test'})
        cls.transverse = Series.create({'name': 'Serie transverse test', 'blog_id': cls.blog.id})

        def post(name, series, published=True, block=False):
            return Post.create({
                'name': name, 'blog_id': cls.blog.id, 'content': '<p>x</p>',
                'series_id': series.id if series else False, 'series_block': block,
                'is_published': published, 'post_date': PAST})

        cls.published = post('Etape publiee alpha', cls.series, block='Bloc installation test')
        cls.draft = post('Etape brouillon omega', cls.series, published=False)
        post('Outil transverse beta', cls.transverse)
        post('Article independant gamma', None)

    def test_parcours_lists_published_posts_only(self):
        response = self.url_open('/parcours')
        self.assertEqual(response.status_code, 200)
        page = response.text
        self.assertIn('Parcours de lecture', page)
        for expected in ('Serie publique dix-neuf', 'Public visé test', 'Description de la série test',
                         'Etape publiee alpha', 'Bloc installation test', 'Serie transverse test',
                         'Toutes versions', 'Articles indépendants récents', 'Article independant gamma',
                         'id="serie-%s"' % self.series.id, self.published.website_url):
            self.assertIn(expected, page)
        self.assertNotIn('Etape brouillon omega', page)

    def test_version_pages(self):
        page_20 = self.url_open('/parcours/odoo-20')
        self.assertEqual(page_20.status_code, 200)
        self.assertIn('Serie transverse test', page_20.text)
        self.assertNotIn('Serie publique dix-neuf', page_20.text)
        self.assertEqual(self.url_open('/parcours/odoo-19').status_code, 200)
        self.assertEqual(self.url_open('/parcours/odoo-99').status_code, 404)

    def test_sitemap_lists_parcours(self):
        website = self.env.ref('website.default_website')
        locs = [page['loc'] for page in website._enumerate_pages(query_string='/parcours')]
        self.assertIn('/parcours', locs)
        self.assertIn('/parcours/odoo-19', locs)
        self.assertIn('/parcours/odoo-20', locs)

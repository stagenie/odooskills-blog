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

    def test_tab_without_slug_is_not_rendered(self):
        # Code dégénéré (majeur vide) : slug calculé à False. La page ne doit
        # jamais produire de lien /parcours/False.
        Version = self.env['oski.blog.odoo.version']
        Series = self.env['oski.blog.series']
        weird = Version.create({'name': 'Édition sans code', 'code': '.0'})
        self.assertFalse(weird.slug)
        weird_series = Series.create({
            'name': 'Serie sans code test', 'blog_id': self.blog.id, 'odoo_version_id': weird.id})
        self.env['blog.post'].create({
            'name': 'Etape sans code', 'blog_id': self.blog.id, 'content': '<p>x</p>',
            'series_id': weird_series.id, 'is_published': True, 'post_date': PAST})
        page = self.url_open('/parcours').text
        # `#{tab.slug}` rend une chaîne vide pour False (pas le texte « False ») :
        # le symptôme est un onglet dont le lien pointe sur /parcours/ tout court.
        self.assertNotIn('href="/parcours/"', page)
        self.assertNotIn('Édition sans code', page)

    def test_version_pages(self):
        page_20 = self.url_open('/parcours/odoo-20')
        self.assertEqual(page_20.status_code, 200)
        self.assertIn('Serie transverse test', page_20.text)
        self.assertNotIn('Serie publique dix-neuf', page_20.text)
        self.assertEqual(self.url_open('/parcours/odoo-19').status_code, 200)
        self.assertEqual(self.url_open('/parcours/odoo-99').status_code, 404)

    def test_sitemap_lists_parcours(self):
        # Odoo 20 n'a pas encore de série propre publiée : pas de doublon avec
        # /parcours (version actuelle) et pas d'entrée pour une version sans contenu.
        website = self.env.ref('website.default_website')
        locs = [page['loc'] for page in website._enumerate_pages(query_string='/parcours')]
        self.assertIn('/parcours', locs)
        self.assertNotIn('/parcours/odoo-19', locs)
        self.assertNotIn('/parcours/odoo-20', locs)

    def test_sitemap_lists_non_current_version_with_own_content(self):
        Series = self.env['oski.blog.series']
        Post = self.env['blog.post']
        series_20 = Series.create({'name': 'Serie sitemap vingt', 'blog_id': self.blog.id,
                                    'odoo_version_id': self.v20.id})
        Post.create({'name': 'Etape vingt sitemap', 'blog_id': self.blog.id, 'content': '<p>x</p>',
                     'series_id': series_20.id, 'is_published': True, 'post_date': PAST})
        website = self.env.ref('website.default_website')
        locs = [page['loc'] for page in website._enumerate_pages(query_string='/parcours')]
        self.assertIn('/parcours', locs)
        self.assertNotIn('/parcours/odoo-19', locs)
        self.assertIn('/parcours/odoo-20', locs)

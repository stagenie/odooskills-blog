from datetime import datetime

from psycopg2 import IntegrityError

from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged
from odoo.tests.common import warmup
from odoo.tools import mute_logger

PAST = datetime(2026, 4, 26, 6, 57)


@tagged('post_install', '-at_install')
class TestBlogBlogParcours(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Blog = cls.env['blog.blog']
        cls.Series = cls.env['oski.blog.series']
        cls.Post = cls.env['blog.post']
        cls.website = cls.env.ref('website.default_website')
        cls.v19 = cls.env.ref('oski_blog_series.odoo_version_19')
        cls.v20 = cls.env.ref('oski_blog_series.odoo_version_20')
        # Neutralise tout parcours déjà publié sur le site (démo, données de recette)
        # pour que les comptes de _oski_chooser_cards restent déterministes ici.
        cls.Series.search([]).write({'active': False})

    def test_slug_is_computed_from_name(self):
        blog = self.Blog.create({'name': 'Développement Odoo'})
        self.assertEqual(blog.parcours_slug, 'developpement-odoo')

    def test_renaming_does_not_change_an_already_set_slug(self):
        blog = self.Blog.create({'name': 'Développement Odoo'})
        self.assertEqual(blog.parcours_slug, 'developpement-odoo')  # calcule et stocke l'adresse
        blog.name = 'Développement Odoo — nouveau nom'
        self.assertEqual(blog.parcours_slug, 'developpement-odoo')

    def test_manually_set_slug_is_kept(self):
        blog = self.Blog.create({'name': 'Développement Odoo', 'parcours_slug': 'adresse-posee-a-la-main'})
        self.assertEqual(blog.parcours_slug, 'adresse-posee-a-la-main')
        blog.name = 'Autre nom'
        self.assertEqual(blog.parcours_slug, 'adresse-posee-a-la-main')

    def test_slug_must_be_unique(self):
        self.Blog.create({'name': 'Premier', 'parcours_slug': 'meme-adresse'})
        with mute_logger('odoo.sql_db'), self.assertRaises(IntegrityError):
            with self.env.cr.savepoint():
                self.Blog.create({'name': 'Second', 'parcours_slug': 'meme-adresse'})

    def test_slug_shaped_like_a_version_is_refused(self):
        with self.assertRaises(ValidationError):
            self.Blog.create({'name': 'Faux', 'parcours_slug': 'odoo-19'})

    def test_parcours_url_of_blog(self):
        blog = self.Blog.create({'name': 'Test url', 'parcours_slug': 'test-url'})
        self.assertEqual(blog._oski_parcours_url(), '/parcours/test-url')
        self.assertEqual(blog._oski_parcours_url(self.v19), '/parcours/test-url')
        self.assertEqual(blog._oski_parcours_url(self.v20), '/parcours/test-url/odoo-20')

    def _series_with_posts(self, blog, name, version=None, count=1):
        series = self.Series.create({
            'name': name, 'blog_id': blog.id, 'odoo_version_id': version.id if version else False})
        for i in range(count):
            self.Post.create({
                'name': '%s - %s' % (name, i), 'blog_id': blog.id, 'content': '<p>x</p>',
                'series_id': series.id, 'series_position': i + 1,
                'is_published': True, 'post_date': PAST})
        return series

    def test_chooser_cards_counts_and_excludes_blog_without_slug_or_series(self):
        blog_a = self.Blog.create({'name': 'Choix A'})
        blog_b = self.Blog.create({'name': 'Choix B'})
        blog_without_slug = self.Blog.create({'name': 'Choix sans adresse', 'parcours_slug': False})
        blog_without_series = self.Blog.create({'name': 'Choix sans série'})
        self._series_with_posts(blog_a, 'Série A1', count=2)
        self._series_with_posts(blog_a, 'Série A2', version=self.v20, count=1)  # pas la version actuelle
        self._series_with_posts(blog_b, 'Série B1', count=3)

        cards = self.Series._oski_chooser_cards(self.website)
        by_blog = {card['blog']: card for card in cards}
        self.assertEqual(set(by_blog), {blog_a, blog_b})
        self.assertEqual(by_blog[blog_a]['series_count'], 1)
        self.assertEqual(by_blog[blog_a]['post_count'], 2)
        self.assertEqual(by_blog[blog_a]['url'], blog_a._oski_parcours_url())
        self.assertEqual(by_blog[blog_b]['series_count'], 1)
        self.assertEqual(by_blog[blog_b]['post_count'], 3)
        self.assertNotIn(blog_without_slug, by_blog)
        self.assertNotIn(blog_without_series, by_blog)

    @warmup
    def test_chooser_cards_query_count(self):
        blog_a = self.Blog.create({'name': 'Perf A'})
        blog_b = self.Blog.create({'name': 'Perf B'})
        for i in range(4):
            self._series_with_posts(blog_a, 'Série perf A%s' % i, count=3)
        for i in range(4):
            self._series_with_posts(blog_b, 'Série perf B%s' % i, count=3)
        self.env.invalidate_all()
        self.assertTrue(self.Series._oski_chooser_cards(self.website))
        with self.assertQueryCount(default=5):
            self.env.invalidate_all()
            self.Series._oski_chooser_cards(self.website)

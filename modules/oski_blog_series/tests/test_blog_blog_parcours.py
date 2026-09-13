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

    # RULING I2 : plus de calcul automatique — l'adresse est un champ simple,
    # facultatif, posé à la main.

    def test_blog_has_no_slug_by_default(self):
        blog = self.Blog.create({'name': 'Blog test sans adresse'})
        self.assertFalse(blog.parcours_slug)

    def test_slug_can_be_set_explicitly(self):
        blog = self.Blog.create({
            'name': 'Blog test avec adresse', 'parcours_slug': 'oski-test-slug-explicite'})
        self.assertEqual(blog.parcours_slug, 'oski-test-slug-explicite')

    def test_slug_bad_format_is_refused(self):
        bad_slugs = (
            'Majuscule-Interdite',      # majuscules interdites
            'espace interdit',          # espace interdit
            'tiret--double',            # tirets simples uniquement
            '-commence-par-tiret',      # ne peut pas commencer par un tiret
            'finit-par-tiret-',         # ne peut pas finir par un tiret
            'accentué',                 # caractères hors [a-z0-9-]
        )
        for bad in bad_slugs:
            with self.subTest(bad=bad), self.assertRaises(ValidationError):
                self.Blog.create({'name': 'Format test', 'parcours_slug': bad})

    def test_slug_shaped_like_a_version_is_refused(self):
        with self.assertRaises(ValidationError):
            self.Blog.create({'name': 'Faux', 'parcours_slug': 'odoo-19'})

    def test_slug_equal_to_an_existing_version_slug_is_refused(self):
        with self.assertRaises(ValidationError):
            self.Blog.create({'name': 'Faux bis', 'parcours_slug': self.v20.slug})

    def test_slug_must_be_unique(self):
        self.Blog.create({'name': 'Premier', 'parcours_slug': 'oski-meme-adresse-test'})
        with mute_logger('odoo.sql_db'), self.assertRaises(IntegrityError):
            with self.env.cr.savepoint():
                self.Blog.create({'name': 'Second', 'parcours_slug': 'oski-meme-adresse-test'})

    def test_copying_a_blog_twice_does_not_duplicate_the_slug(self):
        # RULING I2 : dupliquer un blog deux fois ne doit jamais violer l'unicité —
        # copy=False sur le champ, les copies n'ont pas d'adresse.
        blog = self.Blog.create({'name': 'Original test', 'parcours_slug': 'oski-original-test'})
        copy1 = blog.copy()
        copy2 = blog.copy()
        self.assertFalse(copy1.parcours_slug)
        self.assertFalse(copy2.parcours_slug)

    def test_parcours_url_of_blog(self):
        blog = self.Blog.create({'name': 'Test url', 'parcours_slug': 'oski-test-url'})
        self.assertEqual(blog._oski_parcours_url(), '/parcours/oski-test-url')
        self.assertEqual(blog._oski_parcours_url(self.v19), '/parcours/oski-test-url')
        self.assertEqual(blog._oski_parcours_url(self.v20), '/parcours/oski-test-url/odoo-20')

    def test_parcours_url_is_false_without_slug(self):
        # RULING I3
        blog = self.Blog.create({'name': 'Sans adresse test'})
        self.assertFalse(blog._oski_parcours_url())
        self.assertFalse(blog._oski_parcours_url(self.v20))

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
        blog_a = self.Blog.create({'name': 'Choix A', 'parcours_slug': 'oski-choix-a-test'})
        blog_b = self.Blog.create({'name': 'Choix B', 'parcours_slug': 'oski-choix-b-test'})
        blog_without_slug = self.Blog.create({'name': 'Choix sans adresse'})
        blog_without_series = self.Blog.create({
            'name': 'Choix sans série', 'parcours_slug': 'oski-choix-sans-serie-test'})
        self._series_with_posts(blog_a, 'Série A1', count=2)
        self._series_with_posts(blog_a, 'Série A2', version=self.v20, count=1)  # pas la version actuelle
        self._series_with_posts(blog_b, 'Série B1', count=3)

        cards = self.Series._oski_chooser_cards(self.website)
        by_blog = {card['blog']: card for card in cards}
        self.assertEqual(set(by_blog), {blog_a, blog_b})
        self.assertEqual(by_blog[blog_a]['series_count'], 1)
        self.assertEqual(by_blog[blog_a]['post_count'], 2)
        self.assertEqual(by_blog[blog_a]['url'], '/parcours/oski-choix-a-test')
        self.assertEqual(by_blog[blog_b]['series_count'], 1)
        self.assertEqual(by_blog[blog_b]['post_count'], 3)
        self.assertNotIn(blog_without_slug, by_blog)
        self.assertNotIn(blog_without_series, by_blog)

    @warmup
    def test_chooser_cards_query_count(self):
        blog_a = self.Blog.create({'name': 'Perf A', 'parcours_slug': 'oski-perf-a-test'})
        blog_b = self.Blog.create({'name': 'Perf B', 'parcours_slug': 'oski-perf-b-test'})
        for i in range(4):
            self._series_with_posts(blog_a, 'Série perf A%s' % i, count=3)
        for i in range(4):
            self._series_with_posts(blog_b, 'Série perf B%s' % i, count=3)
        self.env.invalidate_all()
        self.assertTrue(self.Series._oski_chooser_cards(self.website))
        with self.assertQueryCount(default=5):
            self.env.invalidate_all()
            self.Series._oski_chooser_cards(self.website)

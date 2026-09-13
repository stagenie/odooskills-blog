from datetime import datetime

from odoo.tests import HttpCase, tagged

PAST = datetime(2026, 4, 26, 6, 57)


@tagged('post_install', '-at_install')
class TestBlogTemplatesHttp(HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Series = cls.env['oski.blog.series']
        cls.v19 = cls.env.ref('oski_blog_series.odoo_version_19')
        cls.v20 = cls.env.ref('oski_blog_series.odoo_version_20')
        cls.blog = cls.env['blog.blog'].create({'name': 'Blog avec série'})
        cls.plain_blog = cls.env['blog.blog'].create({'name': 'Blog sans série'})
        cls.series = Series.create({'name': 'Serie repere test', 'blog_id': cls.blog.id,
                                    'odoo_version_id': cls.v19.id})
        cls.series_20 = Series.create({'name': 'Serie vingt test', 'blog_id': cls.blog.id,
                                       'odoo_version_id': cls.v20.id})
        cls.first = cls._post('Premiere etape', cls.blog, cls.series)
        cls.second = cls._post('Seconde etape', cls.blog, cls.series)
        cls.standalone = cls._post('Article seul', cls.blog, None)
        cls.plain_post = cls._post('Article ailleurs', cls.plain_blog, None)

    @classmethod
    def _post(cls, name, blog, series, published=True):
        return cls.env['blog.post'].create({
            'name': name, 'blog_id': blog.id, 'content': '<p>x</p>',
            'series_id': series.id if series else False,
            'is_published': published, 'post_date': PAST})

    def test_series_post_shows_step_and_link(self):
        page = self.url_open(self.second.website_url).text
        self.assertIn('o_oski_series_badge', page)
        self.assertIn('Serie repere test', page)
        self.assertIn('étape 2/2', page)
        self.assertIn('%s#serie-%s' % (self.blog._oski_parcours_url(), self.series.id), page)
        self.assertIn('Voir tout le parcours', page)
        self.assertNotIn('Une édition', page)

    def test_standalone_post_has_no_badge(self):
        self.assertNotIn('o_oski_series_badge', self.url_open(self.standalone.website_url).text)

    def test_newer_edition_is_announced(self):
        self.series.replaced_by_id = self.series_20
        self._post('Etape vingt', self.blog, self.series_20)
        page = self.url_open(self.first.website_url).text
        self.assertIn('Écrit pour Odoo 19', page)
        self.assertIn('Une édition Odoo 20 de ce parcours existe', page)
        self.assertIn('%s/odoo-20#serie-%s' % (self.blog._oski_parcours_url(), self.series_20.id), page)

    def test_banner_on_blog_with_series_only(self):
        with_series = self.url_open('/blog/%s' % self.blog.id).text
        self.assertIn('o_oski_parcours_banner', with_series)
        self.assertIn('Suivez un parcours', with_series)
        self.assertIn(self.blog._oski_parcours_url(), with_series)
        self.assertNotIn('o_oski_parcours_banner', self.url_open('/blog/%s' % self.plain_blog.id).text)
        archive = self.url_open(
            '/blog/%s?date_begin=2026-04-01+00%%3A00%%3A00&date_end=2026-04-30+23%%3A59%%3A59' % self.blog.id)
        self.assertEqual(archive.status_code, 200)
        self.assertNotIn('o_oski_parcours_banner', archive.text)

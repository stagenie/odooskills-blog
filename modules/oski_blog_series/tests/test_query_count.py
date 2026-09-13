from datetime import datetime

from odoo.tests import TransactionCase, tagged
from odoo.tests.common import warmup

PAST = datetime(2026, 4, 26, 6, 57)


@tagged('post_install', '-at_install')
class TestQueryCount(TransactionCase):
    """Garde-fou (F2) : le bandeau de liste et le repère d'article ne doivent
    jamais dégénérer en 1 requête par série / article (voir F1)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Series = cls.env['oski.blog.series']
        Post = cls.env['blog.post']
        cls.blog = cls.env['blog.blog'].create({'name': 'Blog perf requêtes'})
        # ~10 séries, chacune avec plusieurs articles publiés au corps volumineux :
        # si `_oski_has_parcours` redevenait O(N séries), ce test le détecterait.
        for i in range(10):
            series = Series.create({'name': 'Série perf %s' % i, 'blog_id': cls.blog.id})
            for j in range(3):
                Post.create({
                    'name': 'Article perf %s-%s' % (i, j), 'blog_id': cls.blog.id,
                    'content': '<p>%s</p>' % ('x' * 2000),
                    'series_id': series.id, 'series_position': j + 1,
                    'is_published': True, 'post_date': PAST,
                })

        cls.badge_series = Series.create({'name': 'Série repère perf', 'blog_id': cls.blog.id})
        cls.badge_posts = cls.env['blog.post']
        for j in range(10):
            cls.badge_posts |= Post.create({
                'name': 'Repère perf %s' % j, 'blog_id': cls.blog.id,
                'content': '<p>%s</p>' % ('x' * 2000),
                'series_id': cls.badge_series.id, 'series_position': j + 1,
                'is_published': True, 'post_date': PAST,
            })

    @warmup
    def test_has_parcours_query_count(self):
        self.env.invalidate_all()
        self.assertTrue(self.blog._oski_has_parcours())
        with self.assertQueryCount(default=2):
            self.env.invalidate_all()
            self.blog._oski_has_parcours()

    @warmup
    def test_series_badge_query_count(self):
        post = self.badge_posts[5]
        self.env.invalidate_all()
        badge = post._oski_series_badge()
        self.assertTrue(badge)
        with self.assertQueryCount(default=5):
            self.env.invalidate_all()
            post._oski_series_badge()

    def test_badge_does_not_load_article_bodies(self):
        series = self.env['oski.blog.series'].create(
            {'name': 'Série repère corps', 'blog_id': self.blog.id})
        first = self.env['blog.post'].create({
            'name': 'Corps repère 1', 'blog_id': self.blog.id,
            'content': '<p>%s</p>' % ('x' * 2000),
            'series_id': series.id, 'series_position': 1,
            'is_published': True, 'post_date': PAST,
        })
        second = self.env['blog.post'].create({
            'name': 'Corps repère 2', 'blog_id': self.blog.id,
            'content': '<p>%s</p>' % ('x' * 2000),
            'series_id': series.id, 'series_position': 2,
            'is_published': True, 'post_date': PAST,
        })
        third = self.env['blog.post'].create({
            'name': 'Corps repère 3', 'blog_id': self.blog.id,
            'content': '<p>%s</p>' % ('x' * 2000),
            'series_id': series.id, 'series_position': 3,
            'is_published': True, 'post_date': PAST,
        })
        posts = first + second + third
        posts.invalidate_recordset()
        badge = second._oski_series_badge()
        self.assertEqual((badge['prev'], badge['next']), (first, third))
        content = self.env['blog.post']._fields['content']
        self.assertFalse(any(self.env.cache.contains(p, content) for p in posts - second))

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
        # F2 : ni le calcul du repère, ni la lecture ultérieure de `.name` /
        # `.website_url` sur `prev`/`next` (ce que font réellement les gabarits
        # QWeb, badge et nav) ne doivent charger le corps HTML des étapes
        # DISTANTES de l'article affiché — série de 5 étapes, repère demandé sur
        # la 3e : les 1re et 5e ne doivent jamais voir leur `content` en cache.
        #
        # `prev`/`next` eux-mêmes finissent par charger leur PROPRE `content` dès
        # que `website_url` est lu : ce champ calculé partage le groupe de
        # préchargement par défaut de `blog.post` avec tous les champs stockés,
        # `content` compris (voir le commentaire dans models/blog_series.py). Ce
        # coût est borné à 2 lignes (les voisins immédiats, déjà nécessaires au
        # rendu), jamais aux N-3 étapes distantes — c'est cette dernière garantie
        # que ce test vérifie, pas l'absence totale de tout chargement de corps.
        series = self.env['oski.blog.series'].create(
            {'name': 'Série repère corps distant', 'blog_id': self.blog.id})
        posts = self.env['blog.post']
        for j in range(5):
            posts |= self.env['blog.post'].create({
                'name': 'Corps repère distant %s' % j, 'blog_id': self.blog.id,
                'content': '<p>%s</p>' % ('x' * 2000),
                'series_id': series.id, 'series_position': j + 1,
                'is_published': True, 'post_date': PAST,
            })
        posts = posts.sorted('series_position')
        far = posts[0] + posts[4]
        posts.invalidate_recordset()
        badge = posts[2]._oski_series_badge()
        self.assertEqual((badge['prev'], badge['next']), (posts[1], posts[3]))
        badge['prev'].name
        badge['next'].name
        badge['prev'].website_url
        badge['next'].website_url
        content = self.env['blog.post']._fields['content']
        self.assertFalse(any(self.env.cache.contains(p, content) for p in far))

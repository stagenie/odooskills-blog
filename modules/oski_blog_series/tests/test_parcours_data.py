from datetime import datetime, timedelta

from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged

PAST = datetime(2026, 4, 26, 6, 57)


@tagged('post_install', '-at_install')
class TestParcoursData(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Post = cls.env['blog.post']
        cls.Series = cls.env['oski.blog.series']
        cls.Version = cls.env['oski.blog.odoo.version']
        cls.website = cls.env.ref('website.default_website')
        cls.v19 = cls.env.ref('oski_blog_series.odoo_version_19')
        cls.v20 = cls.env.ref('oski_blog_series.odoo_version_20')
        cls.blog = cls.env['blog.blog'].create({
            'name': 'Blog données', 'parcours_slug': 'oski-blog-donnees-test'})
        cls.blog_without_series = cls.env['blog.blog'].create({'name': 'Blog sans série'})
        cls.s19 = cls.Series.create({'name': 'S19', 'blog_id': cls.blog.id,
                                     'odoo_version_id': cls.v19.id, 'sequence': 1})
        cls.s_all = cls.Series.create({'name': 'Transverse', 'blog_id': cls.blog.id,
                                       'sequence': 2})
        cls.s20 = cls.Series.create({'name': 'S20', 'blog_id': cls.blog.id,
                                     'odoo_version_id': cls.v20.id, 'sequence': 3})
        cls.s_empty = cls.Series.create({'name': 'Vide', 'blog_id': cls.blog.id,
                                         'odoo_version_id': cls.v19.id, 'sequence': 4})
        cls.p2 = cls._post('Deuxième', cls.s19, 2, block='Bloc A')
        cls.p1 = cls._post('Première', cls.s19, 1, block='Bloc A')
        cls.p3 = cls._post('Troisième', cls.s19, 3, block='Bloc B')
        cls.p_draft = cls._post('Brouillon', cls.s19, 4, published=False)
        cls.p_future = cls._post('Future', cls.s19, 5, date=fields.Datetime.now() + timedelta(days=3))
        cls.p_all = cls._post('Outil', cls.s_all, 1)
        cls.p20 = cls._post('Édition 20', cls.s20, 1)
        cls._post('Brouillon vide', cls.s_empty, 1, published=False)

    @classmethod
    def _post(cls, name, series=None, position=0, block=False, published=True, date=PAST, blog=None):
        return cls.Post.create({
            'name': name, 'blog_id': (blog or cls.blog).id, 'content': '<p>x</p>',
            'series_id': series.id if series else False, 'series_position': position,
            'series_block': block, 'is_published': published, 'post_date': date})

    def test_published_posts_in_reading_order(self):
        self.assertEqual(self.s19._oski_published_posts(), self.p1 | self.p2 | self.p3)
        self.assertEqual(self.s19._oski_published_posts().ids, [self.p1.id, self.p2.id, self.p3.id])

    def test_same_position_falls_back_to_date_then_id(self):
        series = self.Series.create({'name': 'Égalité', 'blog_id': self.blog.id})
        late = self._post('Tard', series, 1, date=PAST + timedelta(hours=1))
        early_b = self._post('Tôt B', series, 1)
        early_a = self._post('Tôt A', series, 1)
        self.assertEqual(series._oski_published_posts().ids, [early_b.id, early_a.id, late.id])

    def test_visible_entries_for_current_version(self):
        entries = self.Series._oski_visible_entries(self.blog, self.v19)
        self.assertEqual([e['series'] for e in entries], [self.s19, self.s_all])

    def test_visible_entries_for_odoo_20(self):
        entries = self.Series._oski_visible_entries(self.blog, self.v20)
        self.assertEqual([e['series'] for e in entries], [self.s_all, self.s20])

    def test_block_title_only_on_first_post_of_block(self):
        rows = self.Series._oski_visible_entries(self.blog, self.v19)[0]['rows']
        self.assertEqual([r['block'] for r in rows], ['Bloc A', False, 'Bloc B'])

    def test_profile_values_cap_independents_at_six(self):
        for i in range(7):
            self._post('Indépendant %s' % i, date=PAST + timedelta(days=i))
        self._post('Indépendant brouillon', published=False, date=PAST + timedelta(days=30))
        self._post('Ailleurs', blog=self.blog_without_series)
        values = self.Series._oski_profile_values(self.blog, self.v19)
        self.assertEqual([e['series'] for e in values['entries']], [self.s19, self.s_all])
        self.assertEqual(values['independents'].mapped('name'),
                         ['Indépendant %s' % i for i in (6, 5, 4, 3, 2, 1)])

    def test_profile_values_for_blog_without_series_has_no_entries(self):
        values = self.Series._oski_profile_values(self.blog_without_series, self.v19)
        self.assertFalse(values['entries'])

    def test_tab_versions(self):
        self.assertEqual(self.Version._oski_tab_versions(self.blog), self.v19 | self.v20)
        self.assertEqual(self.Version._oski_tab_versions(self.blog)[0], self.v19)
        self.p20.is_published = False
        self.assertEqual(self.Version._oski_tab_versions(self.blog), self.v19)

    def test_tab_versions_only_sees_series_of_this_blog(self):
        other_blog = self.env['blog.blog'].create({'name': 'Autre blog tab'})
        other_s20 = self.Series.create({'name': 'S20 autre blog', 'blog_id': other_blog.id,
                                        'odoo_version_id': self.v20.id})
        self._post('Édition 20 autre blog', other_s20, 1, blog=other_blog)
        self.assertEqual(self.Version._oski_tab_versions(other_blog), self.v19 | self.v20)
        # Le blog sans série n'a pas d'onglet 20, même si un AUTRE blog en a un.
        self.assertEqual(self.Version._oski_tab_versions(self.blog_without_series), self.v19)

    def test_badge_of_series_post(self):
        badge = self.p2._oski_series_badge()
        self.assertEqual(badge['series'], self.s19)
        self.assertEqual((badge['step'], badge['total']), (2, 3))
        self.assertEqual(badge['url'], '/parcours/%s#serie-%s' % (self.blog.parcours_slug, self.s19.id))
        self.assertFalse(badge['newer'])

    def test_badge_of_transverse_series_points_to_current_version(self):
        self.assertEqual(self.p_all._oski_series_badge()['url'],
                         '/parcours/%s#serie-%s' % (self.blog.parcours_slug, self.s_all.id))

    def test_no_badge_for_unpublished_or_standalone_post(self):
        self.assertEqual(self.p_draft._oski_series_badge(), {})
        self.assertEqual(self._post('Seul')._oski_series_badge(), {})

    def test_badge_announces_newer_edition_only_when_published(self):
        self.s19.replaced_by_id = self.s20
        badge = self.p1._oski_series_badge()
        self.assertEqual(badge['newer'], self.s20)
        self.assertEqual(badge['newer_url'],
                         '/parcours/%s/odoo-20#serie-%s' % (self.blog.parcours_slug, self.s20.id))
        self.p20.is_published = False
        self.assertFalse(self.p1._oski_series_badge()['newer'])

    def test_blog_has_parcours(self):
        self.assertTrue(self.blog._oski_has_parcours())
        self.assertFalse(self.blog_without_series._oski_has_parcours())

    def test_archived_series_has_no_badge(self):
        self.s19.active = False
        self.assertEqual(self.p1._oski_series_badge(), {})

    def test_archived_series_excluded_from_has_parcours(self):
        only_blog = self.env['blog.blog'].create({'name': 'Blog une seule série'})
        only_series = self.Series.create({'name': 'Seule', 'blog_id': only_blog.id})
        self._post('Article', only_series, 1, blog=only_blog)
        self.assertTrue(only_blog._oski_has_parcours())
        only_series.active = False
        self.assertFalse(only_blog._oski_has_parcours())

    def test_archived_newer_edition_is_treated_as_absent(self):
        self.s19.replaced_by_id = self.s20
        self.s20.active = False
        self.assertFalse(self.p1._oski_series_badge()['newer'])

    def test_replaced_by_cannot_be_self(self):
        with self.assertRaises(ValidationError):
            self.s19.write({'replaced_by_id': self.s19.id})

    def test_badge_has_no_url_when_blog_has_no_slug(self):
        # RULING I3 : le repère existe (étape/total) mais ne pointe nulle part.
        self.assertFalse(self.blog_without_series.parcours_slug)
        series = self.Series.create({'name': 'Serie sans adresse', 'blog_id': self.blog_without_series.id})
        post = self._post('Etape sans adresse', series, 1, blog=self.blog_without_series)
        badge = post._oski_series_badge()
        self.assertEqual((badge['step'], badge['total']), (1, 1))
        self.assertFalse(badge['url'])

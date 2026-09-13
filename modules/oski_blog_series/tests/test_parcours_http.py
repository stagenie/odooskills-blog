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
        cls.blog_slug = 'oski-blog-un-test'
        cls.other_blog_slug = 'oski-blog-deux-test'
        cls.blog = cls.env['blog.blog'].create({
            'name': 'Blog un parcours http', 'parcours_slug': cls.blog_slug})
        cls.other_blog = cls.env['blog.blog'].create({
            'name': 'Blog deux parcours http', 'parcours_slug': cls.other_blog_slug})
        cls.series = Series.create({
            'name': 'Serie publique dix-neuf', 'blog_id': cls.blog.id,
            'odoo_version_id': cls.v19.id, 'audience': 'Public visé test',
            'description': 'Description de la série test'})
        cls.transverse = Series.create({'name': 'Serie transverse test', 'blog_id': cls.blog.id})
        cls.series_20 = Series.create({'name': 'Serie vingt test', 'blog_id': cls.blog.id,
                                       'odoo_version_id': cls.v20.id})
        # other_blog n'a qu'une série transverse : pas de contenu propre à Odoo 20.
        cls.other_series = Series.create({'name': 'Serie autre blog', 'blog_id': cls.other_blog.id})

        def post(name, series, blog=None, published=True, block=False):
            return Post.create({
                'name': name, 'blog_id': (blog or cls.blog).id, 'content': '<p>x</p>',
                'series_id': series.id if series else False, 'series_block': block,
                'is_published': published, 'post_date': PAST})

        cls.published = post('Etape publiee alpha', cls.series, block='Bloc installation test')
        cls.draft = post('Etape brouillon omega', cls.series, published=False)
        post('Outil transverse beta', cls.transverse)
        cls.post_20 = post('Etape vingt publiee', cls.series_20)
        post('Article independant gamma', None)
        post('Article autre blog', cls.other_series, blog=cls.other_blog)

    def test_chooser_lists_both_cards_without_article_titles(self):
        response = self.url_open('/parcours')
        self.assertEqual(response.status_code, 200)
        page = response.text
        self.assertIn('Parcours de lecture', page)
        self.assertIn('Choisissez votre profil', page)
        self.assertIn(self.blog.name, page)
        self.assertIn(self.other_blog.name, page)
        self.assertIn('/parcours/%s' % self.blog_slug, page)
        self.assertIn('/parcours/%s' % self.other_blog_slug, page)
        for title in ('Etape publiee alpha', 'Outil transverse beta', 'Article autre blog'):
            self.assertNotIn(title, page)

    def test_profile_shows_only_its_own_blog_series(self):
        response = self.url_open('/parcours/%s' % self.blog_slug)
        self.assertEqual(response.status_code, 200)
        page = response.text
        for expected in ('Serie publique dix-neuf', 'Public visé test', 'Description de la série test',
                         'Etape publiee alpha', 'Bloc installation test', 'Serie transverse test',
                         'Toutes versions', 'Articles indépendants récents', 'Article independant gamma',
                         'id="serie-%s"' % self.series.id, self.published.website_url,
                         'Autre profil', self.other_blog.name):
            self.assertIn(expected, page)
        self.assertNotIn('Etape brouillon omega', page)
        self.assertNotIn('Serie autre blog', page)
        self.assertNotIn('Article autre blog', page)

    def test_tab_without_slug_is_not_rendered(self):
        Version = self.env['oski.blog.odoo.version']
        Series = self.env['oski.blog.series']
        weird = Version.create({'name': 'Édition sans code', 'code': '.0'})
        self.assertFalse(weird.slug)
        weird_series = Series.create({
            'name': 'Serie sans code test', 'blog_id': self.blog.id, 'odoo_version_id': weird.id})
        self.env['blog.post'].create({
            'name': 'Etape sans code', 'blog_id': self.blog.id, 'content': '<p>x</p>',
            'series_id': weird_series.id, 'is_published': True, 'post_date': PAST})
        page = self.url_open('/parcours/%s' % self.blog_slug).text
        self.assertNotIn('Édition sans code', page)

    def test_unknown_slug_is_404(self):
        self.assertEqual(self.url_open('/parcours/inconnu').status_code, 404)

    def test_blog_of_another_website_is_404(self):
        # M6 : un blog restreint à un autre site n'a pas de page ici.
        other_website = self.env['website'].create({'name': 'Autre site test'})
        isolated = self.env['blog.blog'].create({
            'name': 'Blog autre site', 'parcours_slug': 'oski-blog-autre-site-test',
            'website_id': other_website.id})
        series = self.env['oski.blog.series'].create({'name': 'Serie autre site', 'blog_id': isolated.id})
        self.env['blog.post'].create({
            'name': 'Etape autre site', 'blog_id': isolated.id, 'content': '<p>x</p>',
            'series_id': series.id, 'is_published': True, 'post_date': PAST})
        self.assertEqual(self.url_open('/parcours/oski-blog-autre-site-test').status_code, 404)

    def test_old_version_slug_redirects_to_chooser(self):
        response = self.url_open('/parcours/odoo-19', allow_redirects=False)
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response.headers['Location'], '/parcours')

    def test_version_tab_page(self):
        response = self.url_open('/parcours/%s/odoo-20' % self.blog_slug)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Serie vingt test', response.text)
        self.assertNotIn('Serie publique dix-neuf', response.text)

    def test_current_version_tab_redirects_to_profile(self):
        # RULING I1 : 302 (pas 301) — « actuelle » change dans le temps (Odoo 20
        # deviendra un jour la version actuelle) ; un 301 mis en cache masquerait
        # l'onglet Odoo 19 pour toujours. Seule l'ancienne adresse /parcours/odoo-N
        # (voir test_old_version_slug_redirects_to_chooser) reste un 301.
        response = self.url_open('/parcours/%s/odoo-19' % self.blog_slug, allow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers['Location'], '/parcours/%s' % self.blog_slug)

    def test_unknown_version_tab_is_404(self):
        self.assertEqual(self.url_open('/parcours/%s/odoo-99' % self.blog_slug).status_code, 404)

    def test_version_tab_without_own_content_for_this_blog_is_404(self):
        # M4 : Odoo 20 existe globalement (self.blog en a une série) mais
        # other_blog n'a qu'une série transverse — pas d'onglet Odoo 20 pour lui.
        self.assertEqual(self.url_open('/parcours/%s/odoo-20' % self.other_blog_slug).status_code, 404)

    def test_unknown_blog_with_valid_version_slug_is_404(self):
        # M6
        self.assertEqual(self.url_open('/parcours/inconnu/odoo-20').status_code, 404)

    def test_sitemap_lists_chooser_and_profile_pages_not_old_version_url(self):
        website = self.env.ref('website.default_website')
        locs = [page['loc'] for page in website._enumerate_pages(query_string='/parcours')]
        self.assertIn('/parcours', locs)
        self.assertIn('/parcours/%s' % self.blog_slug, locs)
        self.assertIn('/parcours/%s' % self.other_blog_slug, locs)
        self.assertIn('/parcours/%s/odoo-20' % self.blog_slug, locs)
        self.assertNotIn('/parcours/odoo-19', locs)
        self.assertNotIn('/parcours/odoo-20', locs)


@tagged('post_install', '-at_install')
class TestParcoursChooserSingleBlog(HttpCase):
    """Un seul blog publié avec un parcours : /parcours redirige directement dessus."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Neutralise tout parcours déjà publié sur le site (démo, données de
        # recette) : sans cela, le compte de cartes n'est pas déterministe.
        cls.env['oski.blog.series'].search([]).write({'active': False})
        Series = cls.env['oski.blog.series']
        cls.blog_slug = 'oski-blog-seul-test'
        cls.blog = cls.env['blog.blog'].create({
            'name': 'Blog seul parcours http', 'parcours_slug': cls.blog_slug})
        series = Series.create({'name': 'Serie unique', 'blog_id': cls.blog.id})
        cls.env['blog.post'].create({
            'name': 'Etape unique', 'blog_id': cls.blog.id, 'content': '<p>x</p>',
            'series_id': series.id, 'is_published': True, 'post_date': PAST})

    def test_chooser_redirects_when_only_one_card(self):
        response = self.url_open('/parcours', allow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers['Location'], '/parcours/%s' % self.blog_slug)


@tagged('post_install', '-at_install')
class TestParcoursChooserEmpty(HttpCase):
    """Aucun blog publié n'a de parcours : la page de choix reste servie (200)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Neutralise tout parcours déjà publié sur le site (démo, données de
        # recette) : ce test veut vraiment zéro carte.
        cls.env['oski.blog.series'].search([]).write({'active': False})

    def test_chooser_shows_empty_message_when_no_card(self):
        response = self.url_open('/parcours')
        self.assertEqual(response.status_code, 200)
        self.assertIn("Aucun parcours n'est encore publié.", response.text)


@tagged('post_install', '-at_install')
class TestParcoursBlogWithoutSlug(HttpCase):
    """RULING I2/M6 : un blog sans adresse de parcours n'a ni carte, ni page."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env['oski.blog.series'].search([]).write({'active': False})
        cls.blog = cls.env['blog.blog'].create({'name': 'Blog sans adresse http test'})
        series = cls.env['oski.blog.series'].create({'name': 'Serie sans adresse http', 'blog_id': cls.blog.id})
        cls.env['blog.post'].create({
            'name': 'Etape sans adresse http', 'blog_id': cls.blog.id, 'content': '<p>x</p>',
            'series_id': series.id, 'is_published': True, 'post_date': PAST})

    def test_blog_without_slug_has_no_card(self):
        response = self.url_open('/parcours')
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(self.blog.name, response.text)

    def test_blog_without_slug_has_no_page(self):
        # Il n'a pas d'adresse : aucune clé ne peut le désigner dans l'URL.
        self.assertEqual(self.url_open('/parcours/blog-sans-adresse-http-test').status_code, 404)

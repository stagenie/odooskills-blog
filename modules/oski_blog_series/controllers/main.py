from werkzeug.exceptions import NotFound

from odoo import http
from odoo.http import request


def sitemap_parcours(env, rule, qs):
    """Une entrée par page de parcours : la page de choix, une par blog (version
    actuelle), puis un onglet par blog et version non actuelle ayant du contenu
    propre à ce blog (mêmes onglets que ceux affichés sur la page)."""
    Series = env['oski.blog.series']
    Version = env['oski.blog.odoo.version']
    website = env['website'].get_current_website()
    cards = Series._oski_chooser_cards(website)
    locs = ['/parcours'] + [card['url'] for card in cards]
    for card in cards:
        blog = card['blog']
        for version in Version._oski_tab_versions(blog) - Version._oski_current():
            if version.slug:
                locs.append('%s/%s' % (card['url'], version.slug))
    for loc in locs:
        if not qs or qs.lower() in loc:
            yield {'loc': loc}


class OskiBlogSeriesController(http.Controller):

    @http.route('/parcours', type='http', auth='public', website=True, sitemap=sitemap_parcours)
    def parcours_chooser(self, **kwargs):
        cards = request.env['oski.blog.series']._oski_chooser_cards(request.website)
        if len(cards) == 1:
            return request.redirect(cards[0]['url'], code=302)
        return request.render('oski_blog_series.parcours_chooser', {'cards': cards})

    @http.route('/parcours/<string:key>', type='http', auth='public', website=True)
    def parcours_profile(self, key, **kwargs):
        Version = request.env['oski.blog.odoo.version']
        if Version._oski_from_slug(key):
            # Ancienne adresse /parcours/odoo-19 : la page de choix les remplace.
            return request.redirect('/parcours', code=301)
        blog = self._oski_find_blog(key)
        if not blog:
            raise NotFound()
        return self._oski_render_profile(blog, Version._oski_current())

    @http.route('/parcours/<string:key>/<string:version_slug>', type='http', auth='public', website=True)
    def parcours_profile_version(self, key, version_slug, **kwargs):
        Version = request.env['oski.blog.odoo.version']
        blog = self._oski_find_blog(key)
        version = Version._oski_from_slug(version_slug)
        if not blog or not version:
            raise NotFound()
        current = Version._oski_current()
        if version == current:
            # RULING I1 : 302, pas 301. « Actuelle » change dans le temps (Odoo 20
            # deviendra un jour la version actuelle) ; un 301 mis en cache par un
            # navigateur/CDN masquerait alors l'onglet Odoo 19 pour toujours. Seule
            # l'ancienne adresse /parcours/odoo-N (route à un seul segment,
            # ci-dessus) reste un 301 : elle ne dépend d'aucune version « actuelle ».
            return request.redirect(blog._oski_parcours_url(), code=302)
        # RULING M4 : une version qui existe globalement mais n'a aucun contenu
        # propre à CE blog n'a pas d'onglet ici (cf. _oski_tab_versions(blog)).
        if version not in Version._oski_tab_versions(blog):
            raise NotFound()
        return self._oski_render_profile(blog, version)

    def _oski_find_blog(self, key):
        return request.env['blog.blog'].search(
            request.website.website_domain() + [('parcours_slug', '=', key)], limit=1)

    def _oski_render_profile(self, blog, version):
        Series = request.env['oski.blog.series']
        Version = request.env['oski.blog.odoo.version']
        values = Series._oski_profile_values(blog, version)
        cards = Series._oski_chooser_cards(request.website)
        other_cards = [card for card in cards if card['blog'] != blog]
        return request.render('oski_blog_series.parcours_profile', {
            'blog': blog,
            'version': version,
            'tabs': Version._oski_tab_versions(blog),
            'entries': values['entries'],
            'independents': values['independents'],
            'other_cards': other_cards,
        })

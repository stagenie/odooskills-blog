from werkzeug.exceptions import NotFound

from odoo import http
from odoo.http import request


def sitemap_parcours(env, rule, qs):
    """Une entrée par adresse de parcours ; appelée une seule fois par le site
    (les fonctions de sitemap identiques sont dédoublonnées)."""
    locs = ['/parcours'] + [
        '/parcours/%s' % version.slug
        for version in env['oski.blog.odoo.version'].search([]) if version.slug]
    for loc in locs:
        if not qs or qs.lower() in loc:
            yield {'loc': loc}


class OskiBlogSeriesController(http.Controller):

    @http.route(['/parcours', '/parcours/<string:version_slug>'], type='http', auth='public',
                website=True, sitemap=sitemap_parcours)
    def parcours(self, version_slug=None, **kwargs):
        Version = request.env['oski.blog.odoo.version']
        if version_slug:
            version = Version._oski_from_slug(version_slug)
            if not version:
                raise NotFound()
        else:
            version = Version._oski_current()
        return request.render('oski_blog_series.parcours_page', {
            'version': version,
            'tabs': Version._oski_tab_versions(),
            'sections': request.env['oski.blog.series']._oski_parcours_sections(version, request.website),
        })

import re

from odoo import api, fields, models
from odoo.exceptions import ValidationError

VERSION_SLUG_RE = re.compile(r'odoo-\d+')


class BlogBlog(models.Model):
    _inherit = 'blog.blog'

    parcours_slug = fields.Char(
        string="Adresse du parcours", compute='_compute_parcours_slug', store=True,
        readonly=False, copy=False, index=True,
        help="Adresse de la page de parcours de ce blog : /parcours/<adresse>.")
    parcours_teaser = fields.Char(
        string="Accroche du parcours", translate=True,
        help="Phrase affichée sur la page de choix /parcours, "
             "ex. « Vous développez sur Odoo : ORM, vues, rapports… ».")

    _parcours_slug_unique = models.Constraint(
        'UNIQUE (parcours_slug)',
        "Cette adresse de parcours est déjà utilisée par un autre blog.")

    @api.depends('name')
    def _compute_parcours_slug(self):
        for blog in self:
            if not blog.parcours_slug:
                blog.parcours_slug = self.env['ir.http']._slugify(blog.name or '') or False

    @api.constrains('parcours_slug')
    def _oski_check_parcours_slug_not_version(self):
        for blog in self:
            if blog.parcours_slug and VERSION_SLUG_RE.fullmatch(blog.parcours_slug):
                raise ValidationError(
                    "Cette adresse est réservée aux anciennes adresses de version "
                    "(ex. odoo-19). Choisissez une autre adresse de parcours.")

    def _oski_has_parcours(self):
        """Vrai si le blog a au moins une série visible pour la version actuelle.

        Une seule requête d'existence (COUNT limité à 1, aucune ligne ramenée en
        cache) : pas de recherche de série puis d'article par série, et surtout pas
        de lecture du corps HTML des articles (voir `_oski_published_posts`)."""
        self.ensure_one()
        Post = self.env['blog.post']
        version = self.env['oski.blog.odoo.version']._oski_current()
        domain = [
            ('series_id.blog_id', '=', self.id),
            ('series_id.active', '=', True),
            '|', ('series_id.odoo_version_id', '=', False), ('series_id.odoo_version_id', '=', version.id),
        ] + Post._oski_published_domain()
        return bool(Post.search_count(domain, limit=1))

    def _oski_parcours_url(self, version=None):
        """Adresse de la page de parcours de ce blog, éventuellement pour une version
        non actuelle (la version actuelle n'ajoute jamais de suffixe)."""
        self.ensure_one()
        url = '/parcours/%s' % self.parcours_slug
        current = self.env['oski.blog.odoo.version']._oski_current()
        if version and version != current:
            url += '/%s' % version.slug
        return url

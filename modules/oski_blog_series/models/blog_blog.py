import re

from odoo import api, fields, models
from odoo.exceptions import ValidationError

SLUG_FORMAT_RE = re.compile(r'[a-z0-9]+(?:-[a-z0-9]+)*')
VERSION_SLUG_SHAPE_RE = re.compile(r'odoo-\d+')


class BlogBlog(models.Model):
    _inherit = 'blog.blog'

    parcours_slug = fields.Char(
        string="Adresse du parcours", copy=False, index=True,
        help="Adresse de la page de parcours de ce blog : /parcours/<adresse>. "
             "Vide : pas de page de parcours pour ce blog.")
    parcours_teaser = fields.Char(
        string="Accroche du parcours", translate=True,
        help="Phrase affichée sur la page de choix /parcours, "
             "ex. « Vous développez sur Odoo : ORM, vues, rapports… ».")

    _parcours_slug_unique = models.Constraint(
        'UNIQUE (parcours_slug)',
        "Cette adresse de parcours est déjà utilisée par un autre blog.")

    @api.constrains('parcours_slug')
    def _oski_check_parcours_slug(self):
        # RULING I2 (revue « avec réserves », correctif 1/5) : plus de calcul
        # automatique depuis le nom (collisions possibles entre sites, entre un
        # blog dupliqué et son original, ou avec un blog archivé lors d'un -u —
        # une contrainte UNIQUE viole alors la mise à jour entière). L'adresse est
        # un champ simple, facultatif, posé à la main.
        Version = self.env['oski.blog.odoo.version']
        version_slugs = set(Version.search([]).mapped('slug')) - {False}
        for blog in self:
            slug = blog.parcours_slug
            if not slug:
                continue
            if not SLUG_FORMAT_RE.fullmatch(slug):
                raise ValidationError(
                    "L'adresse de parcours ne peut contenir que des minuscules, "
                    "des chiffres et des tirets simples (ex. « developpement »).")
            if VERSION_SLUG_SHAPE_RE.fullmatch(slug) or slug in version_slugs:
                raise ValidationError(
                    "Cette adresse est réservée à une version d'Odoo (ex. odoo-19). "
                    "Choisissez une autre adresse de parcours.")

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
        non actuelle (la version actuelle n'ajoute jamais de suffixe).

        RULING I3 : renvoie False si le blog n'a pas d'adresse de parcours — un
        blog sans adresse n'a ni carte, ni page, ni lien de bandeau/repère."""
        self.ensure_one()
        if not self.parcours_slug:
            return False
        url = '/parcours/%s' % self.parcours_slug
        current = self.env['oski.blog.odoo.version']._oski_current()
        if version and version != current:
            url += '/%s' % version.slug
        return url

from odoo import api, fields, models
from odoo.exceptions import ValidationError

# Champs suffisants pour afficher /parcours (titre, bloc, tri, lien) sans charger le
# corps HTML de l'article : `content` partage son groupe de préchargement par défaut
# avec les autres champs stockés, donc le lire en accéderait un pour tous les autres.
PARCOURS_POST_FIELDS = ('name', 'blog_id', 'series_position', 'series_block', 'post_date')


class OskiBlogSeries(models.Model):
    _name = 'oski.blog.series'
    _description = "Série d'articles (parcours de lecture)"
    _order = 'sequence, name, id'

    name = fields.Char(string="Nom", required=True, translate=True)
    blog_id = fields.Many2one(
        'blog.blog', string="Blog", required=True, index=True, ondelete='cascade')
    tag_id = fields.Many2one(
        'blog.tag', string="Étiquette de rattachement", ondelete='set null',
        help="Tout article de ce blog qui reçoit cette étiquette rejoint la série.")
    odoo_version_id = fields.Many2one(
        'oski.blog.odoo.version', string="Version d'Odoo", ondelete='restrict',
        help="Vide : la série vaut pour toutes les versions.")
    audience = fields.Char(string="Public visé")
    description = fields.Text(string="Description")
    sequence = fields.Integer(string="Ordre", default=10)
    replaced_by_id = fields.Many2one(
        'oski.blog.series', string="Remplacée par", ondelete='set null',
        help="Édition plus récente de ce parcours (ex. pour Odoo 20).")
    post_ids = fields.One2many('blog.post', 'series_id', string="Articles")
    active = fields.Boolean(default=True)

    _tag_unique = models.Constraint(
        'UNIQUE (tag_id)', "Cette étiquette rattache déjà une autre série.")

    @api.constrains('replaced_by_id')
    def _oski_check_replaced_by_not_self(self):
        for series in self:
            if series.replaced_by_id == series:
                raise ValidationError("Une série ne peut pas être remplacée par elle-même.")

    def _oski_next_position(self, exclude=None):
        """Position suivante dans la série : max des positions + 1."""
        self.ensure_one()
        domain = [('series_id', '=', self.id)]
        if exclude:
            domain.append(('id', 'not in', exclude.ids))
        last = self.env['blog.post'].with_context(active_test=False).search(
            domain, order='series_position desc', limit=1)
        return (last.series_position or 0) + 1

    def _oski_published_posts(self, fields_to_fetch=None):
        """Articles publiés de la série, dans l'ordre de lecture.

        `fields_to_fetch` restreint les colonnes ramenées en cache (ex. pour éviter
        de charger le corps HTML de chaque article, non nécessaire à /parcours)."""
        self.ensure_one()
        Post = self.env['blog.post']
        domain = [('series_id', '=', self.id)] + Post._oski_published_domain()
        order = 'series_position, post_date, id'
        if fields_to_fetch is None:
            return Post.search(domain, order=order)
        return Post.search_fetch(domain, fields_to_fetch, order=order)

    def _oski_parcours_url(self):
        self.ensure_one()
        version = self.odoo_version_id or self.env['oski.blog.odoo.version']._oski_current()
        base = '/parcours/%s' % version.slug if version else '/parcours'
        return '%s#serie-%s' % (base, self.id)

    @api.model
    def _oski_visible_entries(self, blog, version):
        """Séries du blog à montrer pour cette version : la version elle-même ou
        toutes versions, et au moins un article publié."""
        entries = []
        series_list = self.search([
            ('blog_id', '=', blog.id),
            '|', ('odoo_version_id', '=', False), ('odoo_version_id', '=', version.id),
        ])
        for series in series_list:
            posts = series._oski_published_posts(fields_to_fetch=PARCOURS_POST_FIELDS)
            if not posts:
                continue
            rows, previous_block = [], False
            for post in posts:
                block = post.series_block or False
                rows.append({'post': post, 'block': block if block and block != previous_block else False})
                previous_block = block
            entries.append({'series': series, 'posts': posts, 'rows': rows})
        return entries

    @api.model
    def _oski_parcours_sections(self, version, website):
        """Une section par blog du site ayant au moins une série visible."""
        sections = []
        Post = self.env['blog.post']
        for blog in self.env['blog.blog'].search(website.website_domain(), order='id'):
            entries = self._oski_visible_entries(blog, version)
            if not entries:
                continue
            independents = Post.search_fetch([
                ('blog_id', '=', blog.id),
                ('series_id', '=', False),
            ] + Post._oski_published_domain(), PARCOURS_POST_FIELDS,
                order='post_date desc, id desc', limit=6)
            sections.append({'blog': blog, 'series': entries, 'independents': independents})
        return sections

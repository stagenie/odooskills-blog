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
        """Une série transverse ou de la version actuelle pointe vers la page du
        blog sans suffixe de version. RULING I3 : False si le blog n'a pas
        d'adresse de parcours (pas de lien vers une page qui n'existe pas)."""
        self.ensure_one()
        blog_url = self.blog_id._oski_parcours_url(self.odoo_version_id or None)
        if not blog_url:
            return False
        return '%s#serie-%s' % (blog_url, self.id)

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
    def _oski_profile_values(self, blog, version):
        """Valeurs de la page de profil d'un blog pour une version donnée."""
        Post = self.env['blog.post']
        independents = Post.search_fetch([
            ('blog_id', '=', blog.id),
            ('series_id', '=', False),
        ] + Post._oski_published_domain(), PARCOURS_POST_FIELDS,
            order='post_date desc, id desc', limit=6)
        return {
            'entries': self._oski_visible_entries(blog, version),
            'independents': independents,
        }

    @api.model
    def _oski_chooser_cards(self, website):
        """Une carte par blog du site ayant une adresse de parcours et au moins une
        série visible pour la version actuelle.

        Bornée à 3 requêtes SQL (recherche des blogs, `search_fetch` des séries,
        `_read_group` des articles publiés) quel que soit le nombre de blogs/séries :
        pas de recherche de série puis d'articles série par série (voir
        `_oski_has_parcours`), aucun chargement du corps HTML des articles, et
        aucun appel à blog._oski_parcours_url() par carte (mesuré : 5 requêtes au
        total pour cette méthode, tests + accès aux champs des blogs inclus —
        voir tests/test_blog_blog_parcours.py::test_chooser_cards_query_count)."""
        version = self.env['oski.blog.odoo.version']._oski_current()
        Blog = self.env['blog.blog']
        Post = self.env['blog.post']
        blogs = Blog.search(
            website.website_domain() + [('parcours_slug', '!=', False)], order='id')
        if not blogs:
            return []
        series = self.search_fetch([
            ('blog_id', 'in', blogs.ids),
            '|', ('odoo_version_id', '=', False), ('odoo_version_id', '=', version.id),
        ], ['blog_id'])
        if not series:
            return []
        post_counts = {
            series_rec.id: count
            for series_rec, count in Post._read_group(
                [('series_id', 'in', series.ids)] + Post._oski_published_domain(),
                groupby=['series_id'], aggregates=['__count'])
        }
        cards = []
        for blog in blogs:
            counts = [post_counts.get(s.id, 0) for s in series if s.blog_id == blog]
            counts = [c for c in counts if c]
            if not counts:
                continue
            cards.append({
                # Toujours la version actuelle : construite ici sans repasser par
                # blog._oski_parcours_url() (qui interrogerait `_oski_current()` à
                # nouveau pour chaque carte, cassant la borne de requêtes).
                'blog': blog,
                'url': '/parcours/%s' % blog.parcours_slug,
                'series_count': len(counts),
                'post_count': sum(counts),
            })
        return cards

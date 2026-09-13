from odoo import models


class BlogBlog(models.Model):
    _inherit = 'blog.blog'

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

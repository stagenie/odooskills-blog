from odoo import models


class BlogBlog(models.Model):
    _inherit = 'blog.blog'

    def _oski_has_parcours(self):
        """Vrai si le blog a au moins une série visible pour la version actuelle."""
        self.ensure_one()
        version = self.env['oski.blog.odoo.version']._oski_current()
        return bool(self.env['oski.blog.series']._oski_visible_entries(self, version))

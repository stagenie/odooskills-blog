from odoo import fields, models


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

    def _oski_next_position(self, exclude=None):
        """Position suivante dans la série : max des positions + 1."""
        self.ensure_one()
        domain = [('series_id', '=', self.id)]
        if exclude:
            domain.append(('id', 'not in', exclude.ids))
        last = self.env['blog.post'].with_context(active_test=False).search(
            domain, order='series_position desc', limit=1)
        return (last.series_position or 0) + 1

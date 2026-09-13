from odoo import api, fields, models


class BlogPost(models.Model):
    _inherit = 'blog.post'

    series_id = fields.Many2one(
        'oski.blog.series', string="Série", ondelete='set null', index=True, copy=False)
    series_position = fields.Integer(
        string="Étape", copy=False,
        help="Ordre de lecture dans la série. Vide : placé après le dernier article.")
    series_block = fields.Char(
        string="Bloc", help="Facultatif : titre de partie affiché sur /parcours (ex. « Framework ORM »).")

    @api.model_create_multi
    def create(self, vals_list):
        posts = super().create(vals_list)
        posts._oski_apply_series_rules()
        return posts

    def write(self, vals):
        res = super().write(vals)
        if self.env.context.get('oski_series_rules_running'):
            return res
        if {'tag_ids', 'blog_id', 'series_id', 'series_position'} & set(vals):
            # Une série écrite à la main, même vide, est un choix éditorial :
            # l'étiquette ne doit pas la remplacer.
            self._oski_apply_series_rules(link_by_tag='series_id' not in vals)
        return res

    def _oski_apply_series_rules(self, link_by_tag=True):
        """Rattache l'article à la série de son étiquette (même blog, plus petite
        séquence) s'il n'en a pas, puis lui donne la position suivante s'il n'en a pas."""
        Series = self.env['oski.blog.series']
        for post in self.with_context(oski_series_rules_running=True):
            vals = {}
            series = post.series_id
            if not series and link_by_tag and post.tag_ids:
                series = Series.search([
                    ('tag_id', 'in', post.tag_ids.ids),
                    ('blog_id', '=', post.blog_id.id),
                ], order='sequence, id', limit=1)
                if series:
                    vals['series_id'] = series.id
            if series and not post.series_position:
                vals['series_position'] = series._oski_next_position(exclude=post)
            if vals:
                post.write(vals)

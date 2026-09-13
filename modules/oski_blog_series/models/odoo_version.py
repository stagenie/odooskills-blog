from odoo import api, fields, models


class OskiBlogOdooVersion(models.Model):
    _name = 'oski.blog.odoo.version'
    _description = "Version d'Odoo (parcours de lecture)"
    _order = 'sequence, id'

    name = fields.Char(string="Nom", required=True)
    code = fields.Char(
        string="Code", required=True,
        help="Ex. 19.0 — donne l'adresse /parcours/odoo-19.")
    sequence = fields.Integer(string="Ordre", default=10)
    is_current = fields.Boolean(
        string="Version actuelle",
        help="Version affichée par défaut sur /parcours. Une seule à la fois.")
    slug = fields.Char(string="Adresse", compute='_compute_slug')

    _code_unique = models.Constraint('UNIQUE (code)', "Ce code de version existe déjà.")

    @api.depends('code')
    def _compute_slug(self):
        for version in self:
            major = (version.code or '').split('.')[0].strip()
            version.slug = 'odoo-%s' % major if major else False

    @api.model_create_multi
    def create(self, vals_list):
        versions = super().create(vals_list)
        versions.filtered('is_current')[-1:]._oski_make_only_current()
        return versions

    def write(self, vals):
        res = super().write(vals)
        if vals.get('is_current'):
            self[-1:]._oski_make_only_current()
        return res

    def _oski_make_only_current(self):
        """Décoche toutes les autres versions : une seule version actuelle."""
        if not self:
            return
        others = self.search([('is_current', '=', True), ('id', '!=', self.id)])
        if others:
            others.write({'is_current': False})

    @api.model
    def _oski_current(self):
        # Repli explicite par id (première version créée) : `_order` trie par
        # `sequence`, et une version plus récente (ex. Odoo 20) peut porter une
        # séquence plus basse sans être la version actuelle.
        return self.search([('is_current', '=', True)], limit=1) \
            or self.search([], order='id', limit=1)

    @api.model
    def _oski_from_slug(self, slug):
        return self.search([]).filtered(lambda version: version.slug == slug)[:1]

    @api.model
    def _oski_tab_versions(self):
        """Onglets de /parcours : la version actuelle d'abord, puis chaque version
        qui a au moins une série propre avec un article publié."""
        current = self._oski_current()
        Series = self.env['oski.blog.series']
        tabs = self.browse()
        for version in self.search([]):
            if version == current:
                continue
            if any(series._oski_published_posts()
                   for series in Series.search([('odoo_version_id', '=', version.id)])):
                tabs |= version
        return current | tabs

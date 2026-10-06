from odoo import api, fields, models


class LibraryShelf(models.Model):
    _name = 'library.shelf'
    _description = "Rayon"
    _parent_store = True
    _rec_name = 'complete_name'
    _order = 'complete_name'

    name = fields.Char(string="Nom", required=True)
    parent_id = fields.Many2one(
        'library.shelf',
        string="Rayon parent",
        index=True,
        ondelete='restrict',
    )
    parent_path = fields.Char(index=True)
    child_ids = fields.One2many('library.shelf', 'parent_id', string="Sous-rayons")
    complete_name = fields.Char(
        string="Rayon",
        compute='_compute_complete_name',
        recursive=True,
        store=True,
    )
    copy_ids = fields.One2many('library.copy', 'shelf_id', string="Exemplaires")
    copy_count = fields.Integer(
        string="Exemplaires (sous-rayons compris)",
        compute='_compute_copy_count',
    )

    @api.depends('name', 'parent_id.complete_name')
    def _compute_complete_name(self):
        for shelf in self:
            if shelf.parent_id:
                shelf.complete_name = f"{shelf.parent_id.complete_name} / {shelf.name}"
            else:
                shelf.complete_name = shelf.name

    @api.depends_context('hierarchical_naming')
    def _compute_display_name(self):
        if self.env.context.get('hierarchical_naming', True):
            return super()._compute_display_name()
        for shelf in self:
            shelf.display_name = shelf.name

    def _compute_copy_count(self):
        Copy = self.env['library.copy']
        for shelf in self:
            shelf.copy_count = Copy.search_count([('shelf_id', 'child_of', shelf.id)])

    def action_view_copies(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._("Exemplaires de %(shelf)s", shelf=self.complete_name),
            'res_model': 'library.copy',
            'view_mode': 'list,form',
            'domain': [('shelf_id', 'child_of', self.id)],
            'context': {'default_shelf_id': self.id},
        }

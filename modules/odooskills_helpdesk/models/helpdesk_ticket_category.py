from odoo import models, fields, api
from odoo.exceptions import ValidationError


class HelpdeskTicketCategory(models.Model):
    """Catégorie de ticket — modèle hiérarchique (arbre parent/enfants)."""
    _name = 'helpdesk.ticket.category'
    _description = 'Catégorie de ticket helpdesk'
    _order = 'sequence, name'
    _rec_name = 'name'
    _parent_name = 'parent_id'
    _parent_store = True

    _unique_name_parent = models.Constraint(
        'UNIQUE (name, parent_id)',
        "Le nom de la catégorie doit être unique au sein d'un même parent.",
    )

    name = fields.Char(string='Nom', required=True)
    sequence = fields.Integer(string='Séquence', default=10)
    color = fields.Integer(string='Couleur')

    parent_id = fields.Many2one(
        'helpdesk.ticket.category',
        string='Catégorie parente',
        ondelete='cascade',
        index=True,
    )
    parent_path = fields.Char(index=True)
    child_ids = fields.One2many(
        'helpdesk.ticket.category',
        'parent_id',
        string='Sous-catégories',
    )
    complete_name = fields.Char(
        string='Nom complet',
        compute='_compute_complete_name',
        store=True,
        recursive=True,
    )

    @api.depends('name', 'parent_id.complete_name')
    def _compute_complete_name(self):
        for category in self:
            if category.parent_id:
                category.complete_name = f"{category.parent_id.complete_name} / {category.name}"
            else:
                category.complete_name = category.name

    @api.constrains('parent_id')
    def _check_category_recursion(self):
        if not self._check_recursion():
            raise ValidationError(
                "Vous ne pouvez pas créer de catégories récursives."
            )

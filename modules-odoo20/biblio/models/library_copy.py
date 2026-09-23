from odoo import api, fields, models


class LibraryCopy(models.Model):
    _name = 'library.copy'
    _description = "Exemplaire"
    _order = 'book_id, name'

    name = fields.Char(string="Code d'inventaire", required=True, copy=False)
    book_id = fields.Many2one(
        'library.book',
        string="Livre",
        required=True,
        ondelete='cascade',
    )
    state = fields.Selection(
        [
            ('available', "Disponible"),
            ('borrowed', "Emprunté"),
            ('lost', "Perdu"),
        ],
        string="État",
        default='available',
        required=True,
    )
    acquisition_date = fields.Date(
        string="Date d'acquisition",
        default=fields.Date.context_today,
    )

    _name_unique = models.Constraint(
        'UNIQUE(name)',
        "Ce code d'inventaire est déjà utilisé par un autre exemplaire.",
    )

    @api.depends('name', 'book_id.title')
    def _compute_display_name(self):
        for copy in self:
            copy.display_name = f"{copy.name} ({copy.book_id.title})"

from odoo import api, fields, models

class LibraryGenre(models.Model):
    _name = 'library.genre'
    _description = "Genre"
    _order = 'name'

    name = fields.Char(string="Nom", required=True, translate=True)
    color = fields.Integer(string="Couleur")
    book_ids = fields.Many2many(
        'library.book',
        'library_book_genre_rel',
        'genre_id',
        'book_id',
        string="Livres",
    )
    book_count = fields.Integer(string="Nombre de livres", compute='_compute_book_count')

    _name_uniq_index = models.UniqueIndex(
        "((name->>'en_US'))",
        "Ce genre existe déjà.",
    )

    @api.depends('book_ids')
    def _compute_book_count(self):
        for genre in self:
            genre.book_count = len(genre.book_ids)

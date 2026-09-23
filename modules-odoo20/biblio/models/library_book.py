from odoo import api, fields, models


class LibraryBook(models.Model):
    _name = 'library.book'
    _description = "Livre"
    _order = 'title'

    title = fields.Char(string="Titre", required=True)
    author_id = fields.Many2one('res.partner', string="Auteur")
    isbn = fields.Char(string="ISBN", size=13)
    publication_date = fields.Date(string="Date de parution")
    page_count = fields.Integer(string="Nombre de pages")
    summary = fields.Text(string="Résumé")
    active = fields.Boolean(string="Actif", default=True)

    _isbn_unique = models.Constraint(
        'UNIQUE(isbn)',
        "Un ISBN ne peut désigner qu'un seul livre.",
    )

    @api.depends('title', 'author_id')
    def _compute_display_name(self):
        for book in self:
            if book.author_id:
                book.display_name = f"{book.title} — {book.author_id.name}"
            else:
                book.display_name = book.title

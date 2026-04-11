from odoo import models, fields


class Book(models.Model):
    _name = 'library.book'
    _description = 'Livre'

    name = fields.Char(string="Titre", required=True)
    author_name = fields.Char(string="Auteur")
    isbn = fields.Char(string="ISBN")
    publication_date = fields.Date(string="Date de publication")
    pages = fields.Integer(string="Nombre de pages")
    category = fields.Selection([
        ('fiction', 'Fiction'),
        ('tech', 'Technique'),
        ('business', 'Business'),
    ], string="Catégorie")
    active = fields.Boolean(default=True)

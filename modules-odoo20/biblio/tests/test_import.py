import csv

from odoo.tests import TransactionCase
from odoo.tools import BinaryBytes, mute_logger
from odoo.tools.misc import file_open


class TestImport(TransactionCase):
    """Les données du module et l'import du catalogue (fichiers de static/import)."""

    @staticmethod
    def _read(name):
        with file_open(f'biblio/static/import/{name}', 'rb') as f:
            return f.read()

    def _rows(self, name):
        rows = list(csv.reader(self._read(name).decode('utf-8-sig').splitlines()))
        return rows[0], rows[1:]

    def _load(self, model, name):
        fields, data = self._rows(name)
        result = self.env[model].load(fields, data)
        self.assertEqual(result['messages'], [])
        return self.env[model].browse(result['ids'])

    def test_module_data(self):
        self.assertEqual(self.env.ref('biblio.genre_roman').with_context(lang='en_US').name, "Roman")
        self.assertEqual(self.env.ref('biblio.shelf_romans').complete_name, "Fonds général / Romans")
        flags = {
            data.name: data.noupdate
            for data in self.env['ir.model.data'].search([
                ('module', '=', 'biblio'), ('name', 'in', ['genre_roman', 'shelf_romans']),
            ])
        }
        self.assertEqual(flags, {'genre_roman': False, 'shelf_romans': True})

    def test_catalogue(self):
        self._load('res.partner', 'auteurs.csv')
        self.assertEqual(len(self._load('library.book', 'livres.csv')), 5)
        book = self.env.ref('__import__.livre_vingt_mille')
        self.assertEqual(book.author_id, self.env.ref('__import__.auteur_verne'))
        self.assertEqual(
            book.genre_ids,
            self.env.ref('biblio.genre_roman') | self.env.ref('biblio.genre_aventure')
            | self.env.ref('biblio.genre_science_fiction'),
        )
        copies = self._load('library.copy', 'exemplaires.csv')
        self.assertEqual(len(copies), 6)
        self.assertNotIn("Nouveau", copies.mapped('name'))
        self.assertEqual(self.env.ref('__import__.ex_miserables_2').shelf_id, self.env.ref('biblio.shelf_reserve'))

    def test_update_by_external_id(self):
        self._load('res.partner', 'auteurs.csv')
        self._load('library.book', 'livres.csv')
        germinal = self.env.ref('__import__.livre_germinal')
        result = self.env['library.book'].load(['id', 'page_count'], [['livre_germinal', '600']])
        self.assertEqual(result['ids'], germinal.ids)
        self.assertEqual(germinal.page_count, 600)

    def test_missing_author(self):
        fields, data = self._rows('livres.csv')
        result = self.env['library.book'].load(fields, data)
        self.assertFalse(result['ids'])
        self.assertEqual({message['field'] for message in result['messages']}, {'author_id'})
        self.assertIn('auteur_hugo', result['messages'][0]['message'])

    @mute_logger('odoo.sql_db')
    def test_duplicate_isbn_rolls_back_the_file(self):
        self._load('res.partner', 'auteurs.csv')
        fields, data = self._rows('livres.csv')
        data[1][fields.index('isbn')] = data[0][fields.index('isbn')]
        result = self.env['library.book'].load(fields, data)
        self.assertFalse(result['ids'])
        self.assertIn("ISBN", result['messages'][0]['message'])
        self.assertFalse(self.env.ref('__import__.livre_miserables', raise_if_not_found=False))

    def test_module_prefix_refused_by_import(self):
        result = self.env['library.book'].with_context(import_file=True).load(
            ['id', 'title'], [['biblio.livre_essai', "Livre d'essai"]])
        self.assertFalse(result['ids'])
        self.assertIn('biblio.livre_essai', result['messages'][0]['message'])

    def test_import_wizard(self):
        if 'base_import.import' not in self.env:
            self.skipTest("base_import non installé")
        self._load('res.partner', 'auteurs.csv')
        wizard = self.env['base_import.import'].create({
            'res_model': 'library.book',
            'file': BinaryBytes(self._read('livres.csv')),
            'file_name': 'livres.csv',
            'file_type': 'text/csv',
        })
        preview = wizard.parse_preview({'has_headers': True, 'quoting': '"', 'separator': ',', 'encoding': ''})
        self.assertEqual(preview['options']['encoding'], 'utf-8-sig')
        self.assertEqual(preview['preview'][1][0], "Les Misérables")
        fields = ['/'.join(preview['matches'][index]) for index in range(len(preview['headers']))]
        self.assertEqual(fields, preview['headers'])
        result = wizard.execute_import(fields, preview['headers'], preview['options'])
        self.assertEqual(len(result['ids']), 5)
        self.assertEqual(self.env.ref('__import__.livre_miserables').title, "Les Misérables")

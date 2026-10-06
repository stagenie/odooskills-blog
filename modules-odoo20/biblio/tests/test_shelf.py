from odoo.exceptions import UserError

from .common import BiblioCase


class TestShelf(BiblioCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Shelf = cls.env['library.shelf']
        cls.info = Shelf.create({'name': "Informatique"})
        cls.odoo = Shelf.create({'name': "Odoo", 'parent_id': cls.info.id})
        cls.dev = Shelf.create({'name': "Développement", 'parent_id': cls.odoo.id})
        cls.copy_1.shelf_id = cls.dev
        cls.copy_2.shelf_id = cls.odoo

    def test_parent_path(self):
        self.assertEqual(self.dev.parent_path, f"{self.info.id}/{self.odoo.id}/{self.dev.id}/")
        self.assertEqual(self.dev.complete_name, "Informatique / Odoo / Développement")

    def test_child_of(self):
        copies = self.env['library.copy'].search([('shelf_id', 'child_of', self.info.id)])
        self.assertEqual(copies, self.copy_1 | self.copy_2)
        self.assertEqual(self.info.copy_count, 2)
        self.assertEqual(self.dev.copy_count, 1)

    def test_move_subtree(self):
        logiciels = self.env['library.shelf'].create({'name': "Logiciels"})
        self.odoo.parent_id = logiciels
        self.assertEqual(self.dev.parent_path, f"{logiciels.id}/{self.odoo.id}/{self.dev.id}/")
        self.assertEqual(self.dev.complete_name, "Logiciels / Odoo / Développement")
        self.assertEqual(self.info.copy_count, 0)

    def test_no_loop(self):
        with self.assertRaises(UserError):
            self.info.parent_id = self.dev

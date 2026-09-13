from odoo.tests import TransactionCase, tagged

from odoo.addons.oski_blog_series.hooks import PARCOURS_URL, _oski_ensure_parcours_menu


@tagged('post_install', '-at_install')
class TestMenuHook(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Menu = cls.env['website.menu']
        cls.website = cls.env.ref('website.default_website')
        # L'installation a déjà pu créer l'entrée : chaque test part d'un menu connu.
        cls.Menu.search(['|', ('url', '=', PARCOURS_URL), ('url', '=like', '/blog/%')]).unlink()

    def _entries(self):
        return self.Menu.search([('url', '=', PARCOURS_URL), ('website_id', '=', self.website.id)])

    def test_entry_goes_under_parent_of_blog_menus_once(self):
        blog_parent = self.Menu.create({
            'name': 'Blog', 'url': '#', 'parent_id': self.website.menu_id.id,
            'website_id': self.website.id})
        self.Menu.create({
            'name': 'Développement', 'url': '/blog/developpement-odoo-2',
            'parent_id': blog_parent.id, 'website_id': self.website.id})
        _oski_ensure_parcours_menu(self.env)
        _oski_ensure_parcours_menu(self.env)
        entries = self._entries()
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries.parent_id, blog_parent)
        self.assertEqual(entries.name, 'Parcours de lecture')
        self.assertEqual(entries.sequence, 0)

    def test_entry_at_top_level_without_blog_menus(self):
        _oski_ensure_parcours_menu(self.env)
        self.assertEqual(self._entries().parent_id, self.website.menu_id)

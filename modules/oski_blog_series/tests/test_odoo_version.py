from psycopg2 import IntegrityError

from odoo.tests import TransactionCase, tagged
from odoo.tools import mute_logger


@tagged('post_install', '-at_install')
class TestOdooVersion(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Version = cls.env['oski.blog.odoo.version']
        cls.v19 = cls.env.ref('oski_blog_series.odoo_version_19')
        cls.v20 = cls.env.ref('oski_blog_series.odoo_version_20')

    def test_delivered_versions(self):
        self.assertTrue(self.v19.is_current)
        self.assertFalse(self.v20.is_current)
        self.assertEqual(self.v19.slug, 'odoo-19')
        self.assertEqual(self.v20.slug, 'odoo-20')
        self.assertEqual(self.Version._oski_current(), self.v19)

    def test_single_current_on_write(self):
        self.v20.is_current = True
        self.assertTrue(self.v20.is_current)
        self.assertFalse(self.v19.is_current)
        self.assertEqual(self.Version._oski_current(), self.v20)

    def test_single_current_on_create(self):
        v21 = self.Version.create({'name': 'Odoo 21', 'code': '21.0', 'is_current': True})
        self.assertEqual(self.Version.search([('is_current', '=', True)]), v21)

    def test_from_slug(self):
        self.assertEqual(self.Version._oski_from_slug('odoo-20'), self.v20)
        self.assertFalse(self.Version._oski_from_slug('odoo-99'))

    def test_code_is_unique(self):
        with mute_logger('odoo.sql_db'), self.assertRaises(IntegrityError):
            with self.env.cr.savepoint():
                self.Version.create({'name': 'Doublon', 'code': '19.0'})

    def test_current_fallback_picks_lowest_id_not_highest_sequence(self):
        # v20 (séquence 5) est trié avant v19 (séquence 10) par `_order`, mais
        # v19 est la première créée (id le plus bas) : le repli doit la choisir.
        (self.v19 | self.v20).write({'is_current': False})
        self.assertFalse(self.Version.search([('is_current', '=', True)]))
        self.assertEqual(self.Version._oski_current(), self.v19)

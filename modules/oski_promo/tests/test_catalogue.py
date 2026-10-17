from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestOskiCataloguePerEdition(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Isoler le test des produits réels de la base.
        cls.env['product.template'].search([('ebook_ids', '!=', False)]).write({'website_published': False})
        Cat = cls.env['res.partner.category']
        cls.eb19 = cls.env.ref('oski_ebook_lifecycle.ebook_e1')
        cls.eb20 = cls.env['oski.ebook'].create({
            'code': 'T1-20', 'name': 'Test 20',
            'partner_category_id': Cat.create({'name': 'Client T1-20'}).id})
        PT = cls.env['product.template']
        cls.p19 = PT.create({'name': 'Mono 19', 'default_code': 'TCAT-E1', 'website_published': True,
                             'ebook_ids': [(6, 0, cls.eb19.ids)], 'website_sequence': 20})
        cls.p20 = PT.create({'name': 'Mono 20', 'default_code': 'TCAT-E1-20', 'website_published': True,
                             'ebook_ids': [(6, 0, cls.eb20.ids)], 'website_sequence': 10})
        cls.pack = PT.create({'name': 'Pack 20', 'default_code': 'TCAT-PACK-20', 'website_published': True,
                              'ebook_ids': [(6, 0, (cls.eb19 | cls.eb20).ids)], 'website_sequence': 5})

    def test_edition_from_ebook_code(self):
        self.assertEqual(self.p19._oski_edition(), '19')
        self.assertEqual(self.p20._oski_edition(), '20')
        self.assertEqual(self.pack._oski_edition(), '20', "un pack suit l'édition la plus récente")
        self.assertEqual(self.env['product.template'].create({'name': 'x'})._oski_edition(), '')

    def test_grouping_newest_first(self):
        groupes = self.env['website'].oski_catalogue_par_edition()
        self.assertEqual([g['edition'] for g in groupes], ['20', '19'])
        self.assertEqual(groupes[0]['monos'], self.p20)
        self.assertEqual(groupes[0]['packs'], self.pack)
        self.assertEqual(groupes[1]['monos'], self.p19)
        self.assertFalse(groupes[1]['packs'])

    def test_unpublished_edition_disappears(self):
        (self.p20 | self.pack).write({'website_published': False})
        groupes = self.env['website'].oski_catalogue_par_edition()
        self.assertEqual([g['edition'] for g in groupes], ['19'])

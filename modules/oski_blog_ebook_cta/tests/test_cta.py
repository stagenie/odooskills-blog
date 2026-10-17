from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestBlogCta(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        PT = cls.env['product.template']
        # Les produits réels de la base (prod ou recette) ne doivent pas interférer.
        PT.search([('default_code', 'in', [
            'EBOOK-E1', 'EBOOK-E2', 'EBOOK-E3', 'EBOOK-E5', 'PACK-TRILOGIE',
            'EBOOK-E1-20', 'EBOOK-E2-20', 'EBOOK-E3-20', 'PACK-ODOO20'])]).write({'is_published': False})
        cls.e1 = PT.create({'name': 'E1', 'default_code': 'EBOOK-E1', 'is_published': True})
        cls.e2 = PT.create({'name': 'E2', 'default_code': 'EBOOK-E2', 'is_published': True})
        cls.e3 = PT.create({'name': 'E3', 'default_code': 'EBOOK-E3', 'is_published': True})
        cls.e5 = PT.create({'name': 'E5', 'default_code': 'EBOOK-E5', 'is_published': True})
        cls.tri = PT.create({'name': 'Trilogie', 'default_code': 'PACK-TRILOGIE', 'is_published': True})
        cls.e1_20 = PT.create({'name': 'E1-20', 'default_code': 'EBOOK-E1-20', 'is_published': True})
        cls.e2_20 = PT.create({'name': 'E2-20', 'default_code': 'EBOOK-E2-20', 'is_published': True})
        cls.e3_20 = PT.create({'name': 'E3-20', 'default_code': 'EBOOK-E3-20', 'is_published': True})
        cls.pack_20 = PT.create({'name': 'Pack 20', 'default_code': 'PACK-ODOO20', 'is_published': True})
        cls.blog_tech = cls.env['blog.blog'].create({'name': 'Développement Odoo'})
        cls.blog_other = cls.env['blog.blog'].create({'name': 'Voyager'})

    def _post(self, blog, tags=(), name='Art'):
        tag_ids = [(0, 0, {'name': t}) for t in tags]
        return self.env['blog.post'].create({
            'name': name, 'blog_id': blog.id, 'tag_ids': tag_ids})

    def test_tech_blog_maps_e1_e3_edition_20(self):
        prods = self._post(self.blog_tech)._get_ebook_cta_products()
        self.assertEqual(set(prods.mapped('default_code')), {'EBOOK-E1-20', 'EBOOK-E3-20'})

    def test_func_tag_maps_e2_edition_20(self):
        prods = self._post(self.blog_other, tags=['Fonctionnel'])._get_ebook_cta_products()
        self.assertIn('EBOOK-E2-20', prods.mapped('default_code'))

    def test_default_maps_pack_20(self):
        prods = self._post(self.blog_other)._get_ebook_cta_products()
        self.assertEqual(prods.mapped('default_code'), ['PACK-ODOO20'])

    def test_article_odoo_19_keeps_edition_19_and_announces_20(self):
        post = self._post(self.blog_tech, name='Générer un rapport Excel (XLSX) natif dans Odoo 19')
        codes = post._get_ebook_cta_products().mapped('default_code')
        self.assertEqual(codes[0], 'EBOOK-E5', "E5 doit arriver en tête pour un article rapports")
        self.assertIn('EBOOK-E1', codes)
        self.assertNotIn('EBOOK-E1-20', codes)
        self.assertTrue(post._get_ebook_cta_edition_20_available())

    def test_article_v19_tag_is_edition_19(self):
        post = self._post(self.blog_other, tags=['v19', 'Fonctionnel'])
        self.assertEqual(post._get_ebook_cta_edition(), '19')
        self.assertEqual(post._get_ebook_cta_products().mapped('default_code'), ['EBOOK-E2'])

    def test_fallback_to_19_when_20_unpublished(self):
        (self.e1_20 | self.e2_20 | self.e3_20 | self.pack_20).write({'is_published': False})
        prods = self._post(self.blog_tech)._get_ebook_cta_products()
        self.assertEqual(set(prods.mapped('default_code')), {'EBOOK-E1', 'EBOOK-E3'})
        post19 = self._post(self.blog_tech, name='Un article Odoo 19')
        self.assertFalse(post19._get_ebook_cta_edition_20_available())

    def test_edition_20_article_has_no_announcement_line(self):
        self.assertFalse(self._post(self.blog_tech)._get_ebook_cta_edition_20_available())

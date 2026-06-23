from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestBlogCta(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        PT = cls.env['product.template']
        cls.e1 = PT.create({'name': 'E1', 'default_code': 'EBOOK-E1'})
        cls.e2 = PT.create({'name': 'E2', 'default_code': 'EBOOK-E2'})
        cls.e3 = PT.create({'name': 'E3', 'default_code': 'EBOOK-E3'})
        cls.tri = PT.create({'name': 'Trilogie', 'default_code': 'PACK-TRILOGIE'})
        cls.blog_tech = cls.env['blog.blog'].create({'name': 'Développement Odoo'})
        cls.blog_other = cls.env['blog.blog'].create({'name': 'Voyager'})

    def _post(self, blog, tags=()):
        tag_ids = [(0, 0, {'name': t}) for t in tags]
        return self.env['blog.post'].create({
            'name': 'Art', 'blog_id': blog.id, 'tag_ids': tag_ids})

    def test_tech_blog_maps_e1_e3(self):
        prods = self._post(self.blog_tech)._get_ebook_cta_products()
        codes = set(prods.mapped('default_code'))
        self.assertEqual(codes, {'EBOOK-E1', 'EBOOK-E3'})

    def test_func_tag_maps_e2(self):
        prods = self._post(self.blog_other, tags=['Fonctionnel'])._get_ebook_cta_products()
        self.assertIn('EBOOK-E2', prods.mapped('default_code'))

    def test_default_maps_trilogie(self):
        prods = self._post(self.blog_other)._get_ebook_cta_products()
        self.assertEqual(prods.mapped('default_code'), ['PACK-TRILOGIE'])

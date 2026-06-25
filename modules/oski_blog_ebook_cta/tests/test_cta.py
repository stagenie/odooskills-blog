from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestBlogCta(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        PT = cls.env['product.template']
        cls.e1 = PT.create({'name': 'E1', 'default_code': 'EBOOK-E1', 'is_published': True})
        cls.e2 = PT.create({'name': 'E2', 'default_code': 'EBOOK-E2', 'is_published': True})
        cls.e3 = PT.create({'name': 'E3', 'default_code': 'EBOOK-E3', 'is_published': True})
        cls.e5 = PT.create({'name': 'E5', 'default_code': 'EBOOK-E5', 'is_published': True})
        cls.tri = PT.create({'name': 'Trilogie', 'default_code': 'PACK-TRILOGIE', 'is_published': True})
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

    def test_report_title_maps_e5_first(self):
        post = self.env['blog.post'].create({
            'name': 'Générer un rapport Excel (XLSX) natif dans Odoo 19',
            'blog_id': self.blog_tech.id})
        codes = post._get_ebook_cta_products().mapped('default_code')
        self.assertEqual(codes[0], 'EBOOK-E5', "E5 doit arriver en tête pour un article rapports")
        self.assertIn('EBOOK-E1', codes)  # blog tech reste pertinent

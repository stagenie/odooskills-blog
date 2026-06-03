from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestEbookLifecycle(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        ref = cls.env.ref
        cls.cat_e1 = ref('oski_ebook_lifecycle.cat_client_e1')
        cls.cat_e2 = ref('oski_ebook_lifecycle.cat_client_e2')
        cls.cat_e3 = ref('oski_ebook_lifecycle.cat_client_e3')
        cls.cat_pack = ref('oski_ebook_lifecycle.cat_client_pack')
        cls.cat_tri = ref('oski_ebook_lifecycle.cat_client_trilogie')
        cls.eb1 = ref('oski_ebook_lifecycle.ebook_e1')
        cls.eb2 = ref('oski_ebook_lifecycle.ebook_e2')
        cls.eb3 = ref('oski_ebook_lifecycle.ebook_e3')

        ML = cls.env['mailing.list']
        cls.list1 = ML.create({'name': 'TEST Extrait E1'})
        cls.list2 = ML.create({'name': 'TEST Extrait E2'})
        cls.list3 = ML.create({'name': 'TEST Extrait E3'})
        cls.eb1.extract_list_id = cls.list1
        cls.eb2.extract_list_id = cls.list2
        cls.eb3.extract_list_id = cls.list3

        PP = cls.env['product.product']
        cls.p_e1 = PP.create({'name': 'Ebook E1', 'list_price': 20.0,
                              'ebook_ids': [(6, 0, cls.eb1.ids)]})
        cls.p_pack = PP.create({'name': 'Pack E1+E3', 'list_price': 32.0,
                                'ebook_ids': [(6, 0, (cls.eb1 + cls.eb3).ids)],
                                'lifecycle_tier_category_id': cls.cat_pack.id})
        cls.p_tri = PP.create({'name': 'Trilogie', 'list_price': 39.0,
                               'ebook_ids': [(6, 0, (cls.eb1 + cls.eb2 + cls.eb3).ids)],
                               'lifecycle_tier_category_id': cls.cat_tri.id})

        cls.partner = cls.env['res.partner'].create({'name': 'Acheteur', 'email': 'buyer@test.com'})
        cls.contact = cls.env['mailing.contact'].create({
            'name': 'Acheteur',
            'email': 'Buyer@Test.com',
            'subscription_ids': [
                (0, 0, {'list_id': cls.list1.id}),
                (0, 0, {'list_id': cls.list2.id}),
                (0, 0, {'list_id': cls.list3.id}),
            ],
        })

    def _sub(self, mlist):
        return self.env['mailing.subscription'].search([
            ('list_id', '=', mlist.id), ('contact_id', '=', self.contact.id)])

    def _order(self, product):
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {'product_id': product.id, 'product_uom_qty': 1})],
        })
        return order

    def test_mono_e1(self):
        self._order(self.p_e1).action_confirm()
        self.assertIn(self.cat_e1, self.partner.category_id)
        self.assertNotIn(self.cat_pack, self.partner.category_id)
        self.assertTrue(self._sub(self.list1).opt_out)
        self.assertFalse(self._sub(self.list2).opt_out)
        self.assertFalse(self._sub(self.list3).opt_out)

    def test_pack_e1e3(self):
        self._order(self.p_pack).action_confirm()
        cats = self.partner.category_id
        self.assertIn(self.cat_e1, cats)
        self.assertIn(self.cat_e3, cats)
        self.assertIn(self.cat_pack, cats)
        self.assertNotIn(self.cat_e2, cats)
        self.assertTrue(self._sub(self.list1).opt_out)
        self.assertTrue(self._sub(self.list3).opt_out)
        self.assertFalse(self._sub(self.list2).opt_out)

    def test_trilogie(self):
        self._order(self.p_tri).action_confirm()
        cats = self.partner.category_id
        for c in (self.cat_e1, self.cat_e2, self.cat_e3, self.cat_tri):
            self.assertIn(c, cats)
        self.assertTrue(self._sub(self.list1).opt_out)
        self.assertTrue(self._sub(self.list2).opt_out)
        self.assertTrue(self._sub(self.list3).opt_out)

    def test_idempotent(self):
        order = self._order(self.p_e1)
        order.action_confirm()
        order._apply_ebook_lifecycle()
        self.assertEqual(len(self.partner.category_id.filtered(lambda c: c == self.cat_e1)), 1)
        self.assertTrue(self._sub(self.list1).opt_out)

    def test_no_email(self):
        self.partner.email = False
        self._order(self.p_e1).action_confirm()
        self.assertIn(self.cat_e1, self.partner.category_id)

    def test_extensibilite_e4(self):
        cat_e4 = self.env['res.partner.category'].create({'name': 'Client E4'})
        eb4 = self.env['oski.ebook'].create({'code': 'E4', 'name': 'Migration',
                                             'partner_category_id': cat_e4.id})
        p_e4 = self.env['product.product'].create({'name': 'Ebook E4', 'list_price': 22.0,
                                                   'ebook_ids': [(6, 0, eb4.ids)]})
        self._order(p_e4).action_confirm()
        self.assertIn(cat_e4, self.partner.category_id)

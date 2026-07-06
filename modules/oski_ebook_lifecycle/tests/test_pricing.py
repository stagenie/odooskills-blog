from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestOskiPricing(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.eb1 = cls.env.ref('oski_ebook_lifecycle.ebook_e1')
        cls.eb2 = cls.env.ref('oski_ebook_lifecycle.ebook_e2')
        P = cls.env['product.template']
        cls.mono1 = P.create({
            'name': 'TEST E1', 'default_code': 'TEST-E1',
            'ebook_ids': [(6, 0, cls.eb1.ids)],
            'oski_price_regular': 27.0, 'oski_price_launch': 24.0,
        })

    def test_offer_fields_exist_and_store(self):
        self.assertEqual(self.mono1.oski_price_regular, 27.0)
        self.assertEqual(self.mono1.oski_price_launch, 24.0)
        self.assertFalse(self.mono1.oski_launch_deadline)

from odoo.tests import TransactionCase, tagged

from odoo.addons.oski_ebook_lifecycle.hooks import post_init


@tagged('post_install', '-at_install')
class TestPostInit(TransactionCase):

    def test_post_init_cable_listes_et_produits(self):
        ML = self.env['mailing.list']
        ML.create({'name': 'Extrait E1 — Tech'})
        ML.create({'name': 'Extrait E2 — Fonctionnel'})
        ML.create({'name': 'Extrait E3 — Déploiement'})
        PT = self.env['product.template']
        PT.create({'name': 'E1', 'default_code': 'EBOOK-E1', 'list_price': 20})
        pack = PT.create({'name': 'Pack E1+E3', 'default_code': 'PACK-E1E3', 'list_price': 32})
        tri = PT.create({'name': 'Trilogie', 'default_code': 'PACK-TRILOGIE', 'list_price': 39})

        post_init(self.env)

        eb1 = self.env.ref('oski_ebook_lifecycle.ebook_e1')
        self.assertEqual(eb1.extract_list_id.name, 'Extrait E1 — Tech')
        self.assertEqual(set(pack.ebook_ids.mapped('code')), {'E1', 'E3'})
        self.assertEqual(pack.lifecycle_tier_category_id,
                         self.env.ref('oski_ebook_lifecycle.cat_client_pack'))
        self.assertEqual(set(tri.ebook_ids.mapped('code')), {'E1', 'E2', 'E3'})
        self.assertEqual(tri.lifecycle_tier_category_id,
                         self.env.ref('oski_ebook_lifecycle.cat_client_trilogie'))

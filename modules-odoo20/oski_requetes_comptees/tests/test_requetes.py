from odoo.tests import TransactionCase, users, warmup


class RequetesCommon(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        produit = cls.env.ref('product.product_product_4')
        cls.clients = cls.env['res.partner'].create([{'name': f'Client {i}'} for i in range(10)])
        commandes = cls.env['sale.order'].create([
            {'partner_id': client.id, 'order_line': [(0, 0, {'product_id': produit.id})]}
            for client in cls.clients for _ in range(2)
        ])
        commandes.action_confirm()


class TestRequetes(RequetesCommon):

    def test_un_client(self):
        client = self.env['res.partner'].browse(self.clients[0].id)
        with self.assertQueryCount(1):
            self.assertEqual(client.oski_nb_commandes, 2)

    def test_dix_clients(self):
        clients = self.env['res.partner'].browse(self.clients.ids)
        with self.assertQueryCount(1):
            self.assertEqual(clients.mapped('oski_nb_commandes'), [2] * 10)


class TestRequetesUtilisateurs(RequetesCommon):

    @users('admin', 'demo')
    @warmup
    def test_dix_clients(self):
        clients = self.env['res.partner'].browse(self.clients.ids)
        with self.assertQueryCount(admin=1, demo=1):
            clients.mapped('oski_nb_commandes')


class TestRequetesSql(RequetesCommon):

    @users('admin')
    @warmup
    def test_requete_group_by(self):
        clients = self.env['res.partner'].browse(self.clients.ids)
        with self.assertQueries(['''
            SELECT "sale_order"."partner_id", COUNT(*)
            FROM "sale_order"
            WHERE ...
            GROUP BY "sale_order"."partner_id"
            ORDER BY "sale_order"."partner_id" ASC
        ''']):
            clients.mapped('oski_nb_commandes')


class TestRequetesEcriture(RequetesCommon):

    @users('admin')
    @warmup
    def test_ecriture(self):
        client = self.env['res.partner'].browse(self.clients[0].id)
        with self.assertQueryCount(admin=4):
            client.comment = 'Client fidèle'
        with self.assertQueryCount(admin=0, flush=False):
            client.comment = 'Client très fidèle'

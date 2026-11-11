from odoo.tests import HttpCase, tagged


@tagged('post_install', '-at_install')
class TestCodeClientHttp(HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.client = cls.env['res.partner'].create({'name': 'Client du test HTTP'})

    def test_anonyme_renvoye_vers_connexion(self):
        reponse = self.url_open(f'/oski/code-client/{self.client.id}', allow_redirects=False)
        self.assertEqual(reponse.status_code, 303)
        self.assertIn('/web/login', reponse.headers['Location'])

    def test_lecture_json(self):
        self.client.action_oski_generer_code()
        self.authenticate('admin', 'admin')
        reponse = self.url_open(f'/oski/code-client/{self.client.id}')
        self.assertEqual(reponse.status_code, 200)
        self.assertEqual(reponse.json()['code'], self.client.oski_code)

    def test_generer_par_jsonrpc(self):
        self.authenticate('admin', 'admin')
        resultat = self.make_jsonrpc_request('/oski/code-client/generer', {'partner_id': self.client.id})
        self.assertEqual(resultat['code'], 'CLI-%05d' % self.client.id)
        self.assertEqual(self.client.oski_code, resultat['code'])


@tagged('post_install', '-at_install', 'oski_navigateur')
class TestCodeClientTour(HttpCase):

    def test_tour_generer_code(self):
        client = self.env['res.partner'].create({'name': 'Client du tour'})
        self.start_tour(f'/odoo/contacts/{client.id}', 'oski_code_client_tour', login='admin')
        self.assertEqual(client.oski_code, 'CLI-%05d' % client.id)

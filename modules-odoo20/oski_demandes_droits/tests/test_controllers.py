import datetime

from odoo.tests import HttpCase, new_test_user, tagged


@tagged('post_install', '-at_install')
class TestControleursDemandes(HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        groupes = 'base.group_user,oski_demandes_droits.group_demande_user'
        cls.dem_a = new_test_user(cls.env, 'ctl_dem_a', groupes, password='ctl_dem_a-pass')
        cls.dem_b = new_test_user(cls.env, 'ctl_dem_b', groupes)
        cls.demande_a = cls.env['oski.demande'].create({'name': "Écran", 'user_id': cls.dem_a.id})
        cls.demande_b = cls.env['oski.demande'].create({'name': "Casque", 'user_id': cls.dem_b.id})

    def test_json_sa_demande_200_celle_d_un_autre_404(self):
        self.authenticate('ctl_dem_a', 'ctl_dem_a-pass')
        ok = self.url_open(f'/oski/demandes/{self.demande_a.id}/json')
        self.assertEqual(ok.status_code, 200)
        self.assertEqual(ok.json()['name'], "Écran")
        refus = self.url_open(f'/oski/demandes/{self.demande_b.id}/json')
        self.assertEqual(refus.status_code, 404)

    def test_json_anonyme_redirige_vers_la_connexion(self):
        r = self.url_open(f'/oski/demandes/{self.demande_a.id}/json', allow_redirects=False)
        self.assertEqual(r.status_code, 303)
        self.assertIn('/web/login', r.headers['Location'])

    def test_stats_publiques(self):
        r = self.url_open('/oski/demandes/stats')
        self.assertEqual(r.status_code, 200)
        # des comptages par état, aucun champ d'enregistrement
        self.assertLessEqual(set(r.json()), {'draft', 'submitted', 'approved'})
        self.assertTrue(all(isinstance(n, int) for n in r.json().values()))

    def test_api_bearer(self):
        cle = self.env['res.users.apikeys'].with_user(self.dem_a)._generate(
            'rpc', "test", datetime.datetime.now() + datetime.timedelta(days=1))
        r = self.url_open('/oski/api/demandes', headers={'Authorization': f'Bearer {cle}'})
        self.assertEqual(r.status_code, 200)
        self.assertEqual([d['id'] for d in r.json()], [self.demande_a.id])
        self.assertEqual(self.url_open('/oski/api/demandes').status_code, 401)
        mauvaise = self.url_open('/oski/api/demandes', headers={'Authorization': 'Bearer 0000'})
        self.assertEqual(mauvaise.status_code, 401)

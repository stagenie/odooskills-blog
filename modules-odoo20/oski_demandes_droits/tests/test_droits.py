from odoo.exceptions import AccessError
from odoo.tests import TransactionCase, new_test_user, tagged


@tagged('post_install', '-at_install')
class TestDroitsDemandes(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        groupes = 'base.group_user,oski_demandes_droits.group_demande_user'
        cls.societe = cls.env.company
        cls.autre_societe = cls.env['res.company'].create({'name': "Société B"})
        cls.dem_a = new_test_user(cls.env, 'test_dem_a', groupes)
        cls.dem_b = new_test_user(cls.env, 'test_dem_b', groupes)
        cls.valideur = new_test_user(
            cls.env, 'test_valideur', 'base.group_user,oski_demandes_droits.group_demande_valideur')
        Demande = cls.env['oski.demande']
        cls.demande_a = Demande.create({'name': "Écran", 'user_id': cls.dem_a.id})
        cls.demande_b = Demande.create({'name': "Casque", 'user_id': cls.dem_b.id})
        cls.demande_ailleurs = Demande.create({
            'name': "Salon", 'user_id': cls.dem_b.id, 'company_id': cls.autre_societe.id})

    def test_demandeur_ne_voit_que_les_siennes(self):
        Demande = self.env['oski.demande'].with_user(self.dem_a)
        self.assertEqual(Demande.search([]), self.demande_a)
        with self.assertRaises(AccessError):
            self.demande_b.with_user(self.dem_a).read(['name'])
        self.assertFalse(self.demande_b.with_user(self.dem_a).has_access('read'))

    def test_valideur_voit_sa_societe_seulement(self):
        vues = self.env['oski.demande'].with_user(self.valideur).search([])
        self.assertIn(self.demande_a, vues)
        self.assertIn(self.demande_b, vues)
        self.assertNotIn(self.demande_ailleurs, vues)

    def test_demandeur_ne_supprime_pas(self):
        with self.assertRaises(AccessError):
            self.demande_a.with_user(self.dem_a).unlink()

    def test_seul_le_valideur_approuve(self):
        with self.assertRaises(AccessError):
            self.demande_a.with_user(self.dem_a).action_approve()
        with self.assertRaises(AccessError):
            self.demande_a.with_user(self.dem_a).write({'state': 'approved'})
        self.demande_a.with_user(self.valideur).action_approve()
        self.assertEqual(self.demande_a.state, 'approved')

    def test_demande_approuvee_figee_pour_tous(self):
        self.demande_a.with_user(self.valideur).action_approve()
        for user in (self.valideur, self.env.ref('base.user_admin')):
            with self.assertRaises(AccessError):
                self.demande_a.with_user(user).write({'montant': 10})

    def test_types_lisibles_par_tout_le_monde(self):
        self.env['oski.demande.type'].create({'name': "Matériel"})
        Type = self.env['oski.demande.type'].with_user(self.dem_a)
        self.assertTrue(Type.has_access('read'))
        self.assertFalse(Type.has_access('create'))
        self.assertTrue(Type.search([]))

    def test_stats_publiques_sans_enregistrement(self):
        public = self.env.ref('base.public_user')
        stats = self.env['oski.demande'].with_user(public)._stats_publiques()
        self.assertEqual(sum(stats.values()), self.env['oski.demande'].search_count([]))
        self.assertFalse(self.env['oski.demande'].with_user(public).has_access('read'))

from odoo.exceptions import AccessError, UserError
from odoo.tests import Form, TransactionCase, loaded_demo_data, new_test_user, users


class TestCodeClient(TransactionCase):
    """Sans @tagged : étiquettes 'standard' et 'post_install' en Odoo 20."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.client = cls.env['res.partner'].create({'name': 'Client de test'})
        new_test_user(cls.env, login='oski_interne', groups='base.group_user')
        new_test_user(cls.env, login='oski_gestionnaire', groups='base.group_user,base.group_partner_manager')

    def test_generer_code(self):
        self.client.action_oski_generer_code()
        self.assertEqual(self.client.oski_code, 'CLI-%05d' % self.client.id)

    def test_pas_de_second_code(self):
        self.client.action_oski_generer_code()
        with self.assertRaises(UserError):
            self.client.action_oski_generer_code()

    @users('oski_gestionnaire')
    def test_gestionnaire_genere_le_code(self):
        # self.env est ici celui de l'utilisateur : ses droits s'appliquent
        client = self.client.with_env(self.env)
        client.action_oski_generer_code()
        self.assertEqual(client.oski_code, 'CLI-%05d' % client.id)

    @users('oski_interne')
    def test_interne_refuse(self):
        client = self.client.with_env(self.env)
        with self.assertRaises(AccessError):
            client.action_oski_generer_code()

    def test_formulaire_code_en_lecture_seule(self):
        with Form(self.env['res.partner']) as fiche:
            fiche.name = 'Client saisi par Form'
            with self.assertRaises(AssertionError):
                fiche.oski_code = 'CLI-MANUEL'
        self.assertFalse(fiche.record.oski_code)

    def test_contact_de_demo(self):
        if not loaded_demo_data(self.env):
            self.skipTest("base sans données de démonstration")
        azure = self.env.ref('base.res_partner_12')
        azure.action_oski_generer_code()
        self.assertEqual(azure.oski_code, 'CLI-%05d' % azure.id)

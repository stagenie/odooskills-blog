from odoo.exceptions import UserError
from odoo.tests import TransactionCase


class TestMixinSurUnAutreModele(TransactionCase):

    def test_prefixe_du_modele(self):
        document = self.env['test.oski.document'].create({'name': 'Document A'})
        document.action_oski_generer_code()
        self.assertEqual(document.oski_code, 'DOC-%05d' % document.id)

    def test_un_seul_code(self):
        document = self.env['test.oski.document'].create({'name': 'Document B'})
        document.action_oski_generer_code()
        with self.assertRaises(UserError):
            document.action_oski_generer_code()

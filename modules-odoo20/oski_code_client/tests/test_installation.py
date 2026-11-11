from odoo.tests import TransactionCase, tagged


@tagged('at_install', '-post_install')
class TestInstallation(TransactionCase):
    """Lancé juste après l'installation du module, avant les modules qui en dépendent."""

    def test_champ_installe(self):
        self.assertIn('oski_code', self.env['res.partner']._fields)

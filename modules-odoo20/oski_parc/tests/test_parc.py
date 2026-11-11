from odoo.tests import TransactionCase


class TestParc(TransactionCase):

    def test_reference_et_prefixe(self):
        self.env.company.oski_parc_prefixe = 'MAT'
        materiel = self.env['oski.parc.materiel'].create({'name': 'Perceuse', 'numero_serie': 'PE-0103'})
        self.assertEqual(materiel.reference, 'MAT/PE-0103')
        self.env.company.oski_parc_prefixe = 'OUT'
        self.assertEqual(materiel.reference, 'OUT/PE-0103')

    def test_domaine_en_pret(self):
        Materiel = self.env['oski.parc.materiel']
        partner = self.env['res.partner'].create({'name': 'Service technique'})
        Materiel.create([
            {'name': 'Ordinateur portable', 'numero_serie': 'PC-0042', 'partner_id': partner.id},
            {'name': 'Perceuse', 'numero_serie': 'PE-0103'},
        ])
        self.assertEqual(Materiel.search_count(Materiel._domaine_en_pret(partner)), 1)

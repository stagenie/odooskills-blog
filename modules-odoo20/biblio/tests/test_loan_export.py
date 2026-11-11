import base64
import io
from datetime import date, datetime

import openpyxl
from dateutil.relativedelta import relativedelta

from odoo import fields
from odoo.exceptions import AccessError, UserError
from odoo.tests import HttpCase, new_test_user
from odoo.tools import BinaryValue

from .common import BiblioCase


class TestLoanExport(BiblioCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        today = fields.Date.context_today(cls.env['library.loan'])
        cls.copy_3 = cls.env['library.copy'].create({'book_id': cls.book.id})
        cls.loan_late = cls._emprunter(cls.copy_1, date_out=today - relativedelta(days=30))
        cls.loan_ok = cls._emprunter(cls.copy_2, date_out=today - relativedelta(days=2))
        cls.loan_returned = cls._emprunter(cls.copy_3, date_out=today - relativedelta(days=10))
        cls.loan_returned.action_return()
        cls.period = {'date_from': today - relativedelta(days=60), 'date_to': today}

    def _export(self, **vals):
        export = self.env['library.loan.export'].with_user(self.user_manager).create({**self.period, **vals})
        export.action_generate()
        return export

    def _sheet(self, export):
        classeur = openpyxl.load_workbook(io.BytesIO(export.file_data.content))
        return classeur['Emprunts']

    def test_file_is_raw_xlsx(self):
        export = self._export()
        self.assertEqual(export.state, 'get')
        self.assertIsInstance(export.file_data, BinaryValue)
        # Des octets bruts : la signature ZIP d'un .xlsx, pas du base64.
        self.assertEqual(export.file_data.content[:2], b'PK')
        self.assertTrue(export.file_name.endswith('.xlsx'))
        self.assertEqual(export.loan_count, 3)

    def test_workbook_content(self):
        feuille = self._sheet(self._export())
        self.assertEqual(feuille['A1'].value, "Référence")
        self.assertEqual(feuille['I1'].value, "Jours de retard")
        self.assertEqual(feuille.max_row, 5)  # en-tête, 3 emprunts, total
        lignes = {ligne[0].value: ligne for ligne in feuille.iter_rows(min_row=2, max_row=4)}
        retard = lignes[self.loan_late.reference]
        self.assertIsInstance(retard[4].value, datetime)
        self.assertEqual(retard[4].number_format, 'dd/mm/yyyy')
        self.assertEqual(retard[7].value, "En cours")
        self.assertEqual(retard[8].value, self.loan_late.days_late)
        self.assertGreater(retard[8].value, 0)
        rendu = lignes[self.loan_returned.reference]
        self.assertEqual(rendu[6].value.date(), self.loan_returned.date_return)
        self.assertEqual(rendu[7].value, "Rendu")
        self.assertIsNone(lignes[self.loan_ok.reference][6].value)  # pas rendu : cellule vide, pas FAUX
        self.assertEqual(feuille['I5'].value, '=SUM(I2:I4)')
        self.assertEqual(feuille.freeze_panes, 'A2')
        self.assertEqual(feuille.auto_filter.ref, 'A1:I4')
        self.assertEqual(feuille.page_setup.orientation, 'landscape')
        self.assertTrue(feuille.sheet_properties.pageSetUpPr.fitToPage)

    def test_scope_late(self):
        export = self._export(scope='late')
        self.assertEqual(export.loan_count, 1)
        self.assertEqual(self._sheet(export)['A2'].value, self.loan_late.reference)

    def test_no_loan(self):
        export = self.env['library.loan.export'].with_user(self.user_manager).create({
            'date_from': date(2000, 1, 1), 'date_to': date(2000, 1, 31),
        })
        with self.assertRaisesRegex(UserError, "Aucun emprunt"):
            export.action_generate()

    def test_base64_bytes_refused(self):
        export = self._export()
        # L'écriture de la 19.0 : des octets base64 dans un champ Binary.
        with self.assertRaisesRegex(TypeError, "use BinaryValue instead of bytes"):
            export.file_data = base64.b64encode(b"PK...")

    def test_export_private_to_creator(self):
        export = self._export()
        autre = new_test_user(self.env, login='test_biblio_2', groups='biblio.group_library_manager')
        with self.assertRaises(AccessError):
            export.with_user(autre).read(['file_name'])


class TestLoanExportDownload(HttpCase):

    def test_download_url(self):
        new_test_user(self.env, login='biblio_dl', groups='biblio.group_library_manager')
        member = self.env['library.member'].create({'name': "Lecteur", 'card_number': 'T-DL'})
        copy = self.env['library.copy'].create({'book_id': self.env['library.book'].create({'title': "Livre"}).id})
        self.env['library.loan'].create({'member_id': member.id, 'copy_id': copy.id})
        user = self.env['res.users'].search([('login', '=', 'biblio_dl')])
        export = self.env['library.loan.export'].with_user(user).create({})
        export.action_generate()
        action = export.action_download()
        self.assertEqual(action['type'], 'ir.actions.act_url')

        self.authenticate('biblio_dl', 'biblio_dl')
        reponse = self.url_open(action['url'])
        self.assertEqual(reponse.status_code, 200)
        self.assertIn(export.file_name, reponse.headers['Content-Disposition'])
        self.assertEqual(
            reponse.headers['Content-Type'],
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
        self.assertEqual(reponse.content, export.file_data.content)

from .common import BiblioCase


class TestLoanReport(BiblioCase):

    def test_loan_sheet_content(self):
        loan = self._emprunter(self.copy_1)
        contenu, fmt = self.env['ir.actions.report']._render_qweb_pdf(
            'biblio.action_report_library_loan', loan.ids,
        )
        # Sous --test-enable, Odoo rend le HTML au lieu d'appeler wkhtmltopdf.
        self.assertEqual(fmt, 'html')
        self.assertIn(loan.reference, contenu.decode())
        self.assertIn("Python pour Odoo", contenu.decode())

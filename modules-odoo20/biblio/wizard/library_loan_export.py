import io

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.fields import Domain
from odoo.tools import BinaryBytes, date_utils


class LibraryLoanExport(models.TransientModel):
    _name = 'library.loan.export'
    _description = "Exporter les emprunts vers Excel"
    # Explicite : en 20.0, la valeur héritée tombe à 0 dans la tâche de nettoyage.
    _transient_max_hours = 1.0

    date_from = fields.Date(
        string="Emprunts du",
        required=True,
        default=lambda self: date_utils.start_of(fields.Date.context_today(self), 'year'),
    )
    date_to = fields.Date(string="au", required=True, default=fields.Date.context_today)
    scope = fields.Selection(
        [
            ('all', "Tous"),
            ('ongoing', "En cours"),
            ('late', "En retard"),
        ],
        string="Emprunts à inclure",
        default='all',
        required=True,
    )
    state = fields.Selection([('choose', "Choix"), ('get', "Fichier prêt")], default='choose')
    loan_count = fields.Integer(string="Emprunts exportés", readonly=True)
    # Le fichier : des octets bruts dans un BinaryValue, plus de base64 en 20.0.
    file_data = fields.Binary(string="Classeur", readonly=True, attachment=False)
    file_name = fields.Char(string="Nom du fichier", readonly=True)

    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        for export in self:
            if export.date_from > export.date_to:
                raise ValidationError(self.env._("La date de début doit précéder la date de fin."))

    def _get_loans(self):
        self.ensure_one()
        domain = Domain('date_out', '>=', self.date_from) & Domain('date_out', '<=', self.date_to)
        if self.scope == 'ongoing':
            domain &= Domain('state', '=', 'ongoing')
        elif self.scope == 'late':
            domain &= Domain('is_late', '=', True)
        return self.env['library.loan'].search(domain, order='date_out, reference')

    def _build_workbook(self, loans):
        """Rend le classeur .xlsx des emprunts, en octets."""
        import xlsxwriter  # noqa: PLC0415 (dépendance d'Odoo, importée à l'usage comme dans le cœur)

        etats = dict(loans._fields['state']._description_selection(self.env))
        colonnes = [
            (self.env._("Référence"), 16),
            (self.env._("Livre"), 32),
            (self.env._("Exemplaire"), 14),
            (self.env._("Adhérent"), 24),
            (self.env._("Emprunté le"), 13),
            (self.env._("À rendre le"), 13),
            (self.env._("Rendu le"), 13),
            (self.env._("État"), 10),
            (self.env._("Jours de retard"), 15),
        ]
        buffer = io.BytesIO()
        with xlsxwriter.Workbook(buffer, {'in_memory': True}) as classeur:
            feuille = classeur.add_worksheet(self.env._("Emprunts"))
            entete = classeur.add_format({
                'bold': True, 'font_color': '#FFFFFF', 'bg_color': '#017E84', 'border': 1,
            })
            date = classeur.add_format({'num_format': 'dd/mm/yyyy'})
            retard = classeur.add_format({'bold': True, 'font_color': '#B91C1C'})
            total = classeur.add_format({'bold': True, 'top': 1})

            for col, (titre, largeur) in enumerate(colonnes):
                feuille.write(0, col, titre, entete)
                feuille.set_column(col, col, largeur)

            for ligne, emprunt in enumerate(loans, start=1):
                feuille.write_string(ligne, 0, emprunt.reference)
                feuille.write_string(ligne, 1, emprunt.book_id.title or "")
                feuille.write_string(ligne, 2, emprunt.copy_id.name or "")
                feuille.write_string(ligne, 3, emprunt.member_id.name or "")
                for col, valeur in ((4, emprunt.date_out), (5, emprunt.date_due), (6, emprunt.date_return)):
                    if valeur:  # une date vide vaut False : write() l'écrirait comme booléen FAUX
                        feuille.write_datetime(ligne, col, valeur, date)
                feuille.write_string(ligne, 7, etats.get(emprunt.state, ""))
                feuille.write_number(ligne, 8, emprunt.days_late, retard if emprunt.days_late else None)

            fin = len(loans) + 1
            feuille.write_string(fin, 0, self.env._("Total"), total)
            feuille.write_formula(fin, 1, f'=COUNTA(A2:A{fin})', total, len(loans))
            feuille.write_formula(fin, 8, f'=SUM(I2:I{fin})', total, sum(loans.mapped('days_late')))
            feuille.freeze_panes(1, 0)
            feuille.autofilter(0, 0, len(loans), len(colonnes) - 1)
            # À l'impression : A4 paysage, toutes les colonnes sur une page de large.
            feuille.set_paper(9)
            feuille.set_landscape()
            feuille.fit_to_pages(1, 0)
        return buffer.getvalue()

    def action_generate(self):
        self.ensure_one()
        loans = self._get_loans()
        if not loans:
            raise UserError(self.env._("Aucun emprunt ne correspond à ces critères."))
        nom = f"emprunts_{self.date_from:%Y%m%d}_{self.date_to:%Y%m%d}.xlsx"
        self.write({
            'state': 'get',
            'loan_count': len(loans),
            'file_data': BinaryBytes(self._build_workbook(loans), filename=nom),
            'file_name': nom,
        })
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._("Exporter les emprunts"),
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'views': [(False, 'form')],
            'target': 'new',
        }

    def action_download(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{self._name}/{self.id}/file_data/{self.file_name}?download=true',
            'target': 'download',
        }

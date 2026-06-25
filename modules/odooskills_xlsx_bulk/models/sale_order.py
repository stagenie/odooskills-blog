import io

from odoo import api, models, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_export_sales_xlsx_bulk(self):
        """Bouton d'en-tête : télécharge la synthèse de tout le carnet de ventes."""
        return {
            'type': 'ir.actions.act_url',
            'url': '/odooskills/export/sales/xlsx_bulk',
            'target': 'self',
        }

    @api.model
    def _bulk_summary_data(self):
        """Agrège tout le carnet de ventes confirmées en SQL, sans charger les lignes.

        Deux appels `_read_group` font tout le travail côté PostgreSQL :
        - le CA HT et le nombre de lignes par produit ;
        - le CA HT et le nombre de commandes par mois.
        Aucun enregistrement n'est instancié pour le calcul — seules les valeurs
        agrégées remontent. Retourne deux listes de tuples prêtes à écrire.
        """
        line_domain = [('display_type', '=', False),
                       ('order_id.state', 'in', ('sale', 'done'))]
        product_groups = self.env['sale.order.line']._read_group(
            line_domain,
            groupby=['product_id'],
            aggregates=['price_subtotal:sum', '__count'],
        )
        products = sorted(
            ((product.display_name, count, subtotal)
             for product, subtotal, count in product_groups),
            key=lambda r: r[2], reverse=True,
        )

        order_domain = [('state', 'in', ('sale', 'done'))]
        month_groups = self.env['sale.order']._read_group(
            order_domain,
            groupby=['date_order:month'],
            aggregates=['amount_untaxed:sum', '__count'],
        )
        months = [
            ((period.strftime('%m/%Y') if period else _('Inconnu')), count, untaxed)
            for period, untaxed, count in month_groups
        ]
        return products, months

    def _build_sales_xlsx_bulk(self):
        """Construit la synthèse Excel en mode mémoire constante.

        Le mode `constant_memory` d'xlsxwriter écrit chaque ligne sur le disque
        dès qu'elle est terminée plutôt que de garder tout le classeur en RAM :
        l'empreinte mémoire reste plate quel que soit le volume. Contrainte :
        écrire les cellules ligne par ligne, dans l'ordre croissant. Retourne
        les octets (`bytes`) du .xlsx.
        """
        import xlsxwriter  # vendored par Odoo

        products, months = self._bulk_summary_data()

        buffer = io.BytesIO()
        workbook = xlsxwriter.Workbook(
            buffer, {'in_memory': True, 'constant_memory': True})

        title_fmt = workbook.add_format({
            'bold': True, 'font_size': 13, 'font_color': '#FFFFFF',
            'bg_color': '#1D6F42', 'align': 'left', 'valign': 'vcenter',
        })
        header_fmt = workbook.add_format({
            'bold': True, 'font_color': '#FFFFFF', 'bg_color': '#2E7D54', 'border': 1,
        })
        text_fmt = workbook.add_format({'border': 1})
        int_fmt = workbook.add_format({'num_format': '#,##0', 'border': 1})
        money_fmt = workbook.add_format({'num_format': '#,##0.00\\ €', 'border': 1})
        total_lbl_fmt = workbook.add_format({
            'bold': True, 'bg_color': '#E8F3EC', 'border': 1, 'align': 'right',
        })
        total_money_fmt = workbook.add_format({
            'bold': True, 'bg_color': '#E8F3EC', 'num_format': '#,##0.00\\ €', 'border': 1,
        })

        self._write_summary(
            workbook, _('Synthèse produit'),
            _('Synthèse du CA par produit — ventes confirmées'),
            _('Produit'), products,
            title_fmt, header_fmt, text_fmt, int_fmt, money_fmt,
            total_lbl_fmt, total_money_fmt,
        )
        self._write_summary(
            workbook, _('Synthèse mensuelle'),
            _('Synthèse du CA par mois — ventes confirmées'),
            _('Mois'), months,
            title_fmt, header_fmt, text_fmt, int_fmt, money_fmt,
            total_lbl_fmt, total_money_fmt,
        )

        workbook.close()
        data = buffer.getvalue()
        buffer.close()
        return data

    def _write_summary(self, workbook, sheet_name, title, label, rows,
                       title_fmt, header_fmt, text_fmt, int_fmt, money_fmt,
                       total_lbl_fmt, total_money_fmt):
        """Écrit une feuille de synthèse en flux (cellules en ordre croissant).

        En mode `constant_memory`, on écrit chaque ligne de haut en bas : titre,
        en-tête, lignes agrégées, puis total. Le `merge_range` du titre reste
        permis car il porte sur la ligne 0, écrite avant toute autre.
        """
        sheet = workbook.add_worksheet(sheet_name)
        # Largeurs définies avant l'écriture des lignes (contrainte du flux).
        sheet.set_column(0, 0, 42)
        sheet.set_column(1, 1, 12)
        sheet.set_column(2, 2, 18)

        # merge_range reste possible ici car la ligne 0 est écrite en premier,
        # avant toute autre ligne (contrainte du mode flux).
        sheet.merge_range(0, 0, 0, 2, title, title_fmt)
        sheet.set_row(0, 22)
        sheet.write(1, 0, label, header_fmt)
        sheet.write(1, 1, _('Nombre'), header_fmt)
        sheet.write(1, 2, _('CA HT'), header_fmt)

        row = 2
        total_amount = 0.0
        total_count = 0
        for name, count, amount in rows:
            sheet.write(row, 0, name, text_fmt)
            sheet.write_number(row, 1, count, int_fmt)
            sheet.write_number(row, 2, amount, money_fmt)
            total_amount += amount
            total_count += count
            row += 1

        sheet.write(row, 0, _('Total'), total_lbl_fmt)
        sheet.write_number(row, 1, total_count, total_lbl_fmt)
        sheet.write_number(row, 2, total_amount, total_money_fmt)

import io
import re

from odoo import models, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_export_lines_xlsx_sheets(self):
        """Bouton d'en-tête : télécharge le classeur XLSX multi-feuilles."""
        ids = ','.join(str(i) for i in self.ids)
        return {
            'type': 'ir.actions.act_url',
            'url': '/odooskills/export/sale_lines/xlsx_sheets?order_ids=%s' % ids,
            'target': 'self',
        }

    @staticmethod
    def _safe_sheet_name(name, used):
        """Nettoie un nom de feuille Excel : 31 car. max, sans []:*?/\\ et unique.

        Excel refuse ces caractères et deux feuilles de même nom. On tronque
        puis on suffixe ` (2)`, ` (3)`… en cas de collision après nettoyage.
        """
        clean = re.sub(r'[\[\]:*?/\\]', ' ', name or _('Sans commercial')).strip()
        clean = (clean or _('Sans commercial'))[:31]
        candidate, n = clean, 1
        while candidate.lower() in used:
            n += 1
            suffix = ' (%d)' % n
            candidate = clean[:31 - len(suffix)] + suffix
        used.add(candidate.lower())
        return candidate

    def _build_sale_lines_xlsx_sheets(self):
        """Construit un classeur Excel à plusieurs feuilles.

        Les commandes sont regroupées par commercial : une feuille par
        commercial (lignes + total), plus une feuille « Sommaire » en tête
        qui liste chaque groupe avec un lien interne (`write_url`) vers sa
        feuille et son total. Retourne les octets (`bytes`) du .xlsx.
        """
        import xlsxwriter  # vendored par Odoo

        buffer = io.BytesIO()
        workbook = xlsxwriter.Workbook(buffer, {'in_memory': True})

        # --- Palette de formats partagée entre toutes les feuilles ----------
        title_fmt = workbook.add_format({
            'bold': True, 'font_size': 14, 'font_color': '#FFFFFF',
            'bg_color': '#1D6F42', 'align': 'center', 'valign': 'vcenter',
        })
        header_fmt = workbook.add_format({
            'bold': True, 'font_color': '#FFFFFF', 'bg_color': '#2E7D54',
            'border': 1, 'align': 'center', 'valign': 'vcenter', 'text_wrap': True,
        })
        text_fmt = workbook.add_format({'border': 1})
        date_fmt = workbook.add_format({'num_format': 'dd/mm/yyyy', 'border': 1})
        money_fmt = workbook.add_format({'num_format': '#,##0.00\\ €', 'border': 1})
        total_lbl_fmt = workbook.add_format({
            'bold': True, 'bg_color': '#E8F3EC', 'border': 1, 'align': 'right',
        })
        total_money_fmt = workbook.add_format({
            'bold': True, 'bg_color': '#E8F3EC', 'num_format': '#,##0.00\\ €', 'border': 1,
        })
        link_fmt = workbook.add_format({'font_color': '#1D6F42', 'underline': 1, 'border': 1})

        # --- Regroupement des commandes par commercial ----------------------
        groups = {}
        for order in self:
            commercial = order.user_id.name or _('Sans commercial')
            groups.setdefault(commercial, self.env['sale.order'])
            groups[commercial] |= order
        # Ordre stable : alphabétique sur le nom du commercial.
        ordered = sorted(groups.items(), key=lambda kv: kv[0].lower())

        headers = [
            _('Commande'), _('Date'), _('Client'), _('Produit'),
            _('Quantité'), _('Total HT'),
        ]

        # --- Feuille sommaire créée EN PREMIER : l'ordre de création fixe ----
        # l'ordre des onglets dans xlsxwriter, donc le sommaire reste en tête.
        # On la remplit après coup, une fois les totaux par feuille connus.
        summary = workbook.add_worksheet(_('Sommaire'))
        summary.activate()

        # --- Une feuille de détail par commercial ---------------------------
        used_names = {_('sommaire')}  # réserve le nom de la feuille d'accueil
        summary_rows = []  # (sheet_name, nb_commandes, total_ht)
        for commercial, orders in ordered:
            sheet_name = self._safe_sheet_name(commercial, used_names)
            sheet = workbook.add_worksheet(sheet_name)
            total = self._fill_detail_sheet(
                sheet, commercial, orders, headers,
                title_fmt, header_fmt, text_fmt, date_fmt, money_fmt,
                total_lbl_fmt, total_money_fmt,
            )
            summary_rows.append((sheet_name, len(orders), total))

        # --- Remplissage différé de la feuille sommaire ---------------------
        self._fill_summary_sheet(
            summary, summary_rows, title_fmt, header_fmt,
            text_fmt, money_fmt, total_lbl_fmt, total_money_fmt, link_fmt,
        )

        workbook.close()
        data = buffer.getvalue()
        buffer.close()
        return data

    def _fill_detail_sheet(self, sheet, commercial, orders, headers,
                           title_fmt, header_fmt, text_fmt, date_fmt, money_fmt,
                           total_lbl_fmt, total_money_fmt):
        """Remplit une feuille de détail pour un commercial. Renvoie le total HT."""
        last_col = len(headers) - 1
        sheet.merge_range(
            0, 0, 0, last_col,
            _('Commandes — %s') % commercial, title_fmt,
        )
        sheet.set_row(0, 24)
        for col, label in enumerate(headers):
            sheet.write(1, col, label, header_fmt)
        widths = [len(h) for h in headers]

        row = 2
        total_ht = 0.0
        for order in orders:
            for line in order.order_line.filtered(lambda l: not l.display_type):
                total_ht += line.price_subtotal
                date = order.date_order.date() if order.date_order else None
                values = [
                    order.name, date, order.partner_id.display_name,
                    line.product_id.display_name or line.name,
                    line.product_uom_qty, line.price_subtotal,
                ]
                sheet.write(row, 0, values[0], text_fmt)
                sheet.write_datetime(row, 1, date, date_fmt) if date else sheet.write(row, 1, '', text_fmt)
                sheet.write(row, 2, values[2], text_fmt)
                sheet.write(row, 3, values[3], text_fmt)
                sheet.write_number(row, 4, values[4], text_fmt)
                sheet.write_number(row, 5, values[5], money_fmt)
                for col, value in enumerate(values):
                    widths[col] = max(widths[col], len(str(value or '')))
                row += 1

        first_data_row, last_data_row = 2, row - 1
        if last_data_row >= first_data_row:
            sheet.write(row, 0, _('Total'), total_lbl_fmt)
            for col in range(1, last_col):
                sheet.write_blank(row, col, None, total_lbl_fmt)
            sheet.write_formula(
                row, last_col,
                '=SUM(F%d:F%d)' % (first_data_row + 1, last_data_row + 1),
                total_money_fmt, value=total_ht,
            )

        for col, width in enumerate(widths):
            sheet.set_column(col, col, min(width + 2, 50))
        sheet.freeze_panes(2, 0)

        # Impression : paysage, largeur ajustée, titre + en-tête répétés.
        sheet.set_landscape()
        sheet.fit_to_pages(1, 0)
        sheet.repeat_rows(0, 1)
        return total_ht

    def _fill_summary_sheet(self, sheet, summary_rows, title_fmt, header_fmt,
                            text_fmt, money_fmt, total_lbl_fmt, total_money_fmt, link_fmt):
        """Feuille d'accueil : une ligne par feuille de détail, avec lien interne."""
        cols = [_('Commercial'), _('Commandes'), _('Total HT')]
        sheet.merge_range(0, 0, 0, len(cols) - 1, _('Sommaire par commercial'), title_fmt)
        sheet.set_row(0, 24)
        for col, label in enumerate(cols):
            sheet.write(1, col, label, header_fmt)

        row = 2
        grand_total = 0.0
        for sheet_name, nb_orders, total in summary_rows:
            grand_total += total
            # Lien interne : `internal:'Nom feuille'!A1`. Les apostrophes
            # internes au nom sont doublées, comme dans une formule Excel.
            target = "internal:'%s'!A1" % sheet_name.replace("'", "''")
            sheet.write_url(row, 0, target, link_fmt, sheet_name)
            sheet.write_number(row, 1, nb_orders, text_fmt)
            sheet.write_number(row, 2, total, money_fmt)
            row += 1

        if summary_rows:
            sheet.write(row, 0, _('Total général'), total_lbl_fmt)
            sheet.write_blank(row, 1, None, total_lbl_fmt)
            sheet.write_number(row, 2, grand_total, total_money_fmt)

        sheet.set_column(0, 0, 28)
        sheet.set_column(1, 1, 12)
        sheet.set_column(2, 2, 16)
        sheet.freeze_panes(2, 0)

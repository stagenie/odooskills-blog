import io

from odoo import models, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_export_lines_xlsx_pro(self):
        """Bouton d'en-tête : télécharge le rapport XLSX mis en forme."""
        ids = ','.join(str(i) for i in self.ids)
        return {
            'type': 'ir.actions.act_url',
            'url': '/odooskills/export/sale_lines/xlsx_pro?order_ids=%s' % ids,
            'target': 'self',
        }

    def _build_sale_lines_xlsx_pro(self):
        """Construit un classeur Excel mis en forme des lignes de commande.

        Démontre la mise en forme avancée d'`xlsxwriter` : titre fusionné,
        volets figés, formats monétaires / pourcentage / date, formatage
        conditionnel et ligne de totaux par formule. Retourne les octets
        (`bytes`) du fichier .xlsx.
        """
        import xlsxwriter  # vendored par Odoo

        buffer = io.BytesIO()
        workbook = xlsxwriter.Workbook(buffer, {'in_memory': True})
        sheet = workbook.add_worksheet(_('Lignes de vente'))

        # --- Palette de formats réutilisables -------------------------------
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
        pct_fmt = workbook.add_format({'num_format': '0.0"%"', 'border': 1})
        total_lbl_fmt = workbook.add_format({
            'bold': True, 'bg_color': '#E8F3EC', 'border': 1, 'align': 'right',
        })
        total_money_fmt = workbook.add_format({
            'bold': True, 'bg_color': '#E8F3EC', 'num_format': '#,##0.00\\ €', 'border': 1,
        })

        headers = [
            _('Commande'), _('Date'), _('Client'), _('Produit'),
            _('Quantité'), _('Prix unitaire'), _('Remise %'), _('Total HT'),
        ]

        # --- Ligne 0 : titre fusionné sur toute la largeur ------------------
        last_col = len(headers) - 1
        sheet.merge_range(
            0, 0, 0, last_col,
            _('Rapport des lignes de vente — %s') % self.env.company.name,
            title_fmt,
        )
        sheet.set_row(0, 24)

        # --- Ligne 1 : en-têtes de colonnes ---------------------------------
        for col, label in enumerate(headers):
            sheet.write(1, col, label, header_fmt)
        widths = [len(h) for h in headers]

        # --- Lignes de données ----------------------------------------------
        row = 2
        total_ht = 0.0
        for order in self:
            for line in order.order_line.filtered(lambda l: not l.display_type):
                total_ht += line.price_subtotal
                date = order.date_order.date() if order.date_order else None
                values = [
                    order.name,
                    date,
                    order.partner_id.display_name,
                    line.product_id.display_name or line.name,
                    line.product_uom_qty,
                    line.price_unit,
                    line.discount,
                    line.price_subtotal,
                ]
                sheet.write(row, 0, values[0], text_fmt)
                sheet.write_datetime(row, 1, date, date_fmt) if date else sheet.write(row, 1, '', text_fmt)
                sheet.write(row, 2, values[2], text_fmt)
                sheet.write(row, 3, values[3], text_fmt)
                sheet.write_number(row, 4, values[4], text_fmt)
                sheet.write_number(row, 5, values[5], money_fmt)
                sheet.write_number(row, 6, values[6], pct_fmt)
                sheet.write_number(row, 7, values[7], money_fmt)
                for col, value in enumerate(values):
                    widths[col] = max(widths[col], len(str(value or '')))
                row += 1

        first_data_row, last_data_row = 2, row - 1

        # --- Ligne de totaux : libellé + formule SUM ------------------------
        if last_data_row >= first_data_row:
            sheet.write(row, 0, _('Total'), total_lbl_fmt)
            for col in range(1, 7):
                sheet.write_blank(row, col, None, total_lbl_fmt)
            # On passe aussi la valeur calculée (`value=`) : xlsxwriter ne
            # calcule pas les formules, le tableur afficherait 0 jusqu'au
            # premier recalcul sans cette valeur en cache.
            sheet.write_formula(
                row, 7,
                '=SUM(H%d:H%d)' % (first_data_row + 1, last_data_row + 1),
                total_money_fmt,
                value=total_ht,
            )

            # --- Formatage conditionnel : dégradé sur la colonne Total HT ---
            sheet.conditional_format(
                first_data_row, 7, last_data_row, 7,
                {'type': '3_color_scale',
                 'min_color': '#FFFFFF', 'mid_color': '#A8D5BA', 'max_color': '#1D6F42'},
            )

        # --- Largeurs + volets figés sous l'en-tête -------------------------
        for col, width in enumerate(widths):
            sheet.set_column(col, col, min(width + 2, 50))
        sheet.freeze_panes(2, 0)

        # --- Mise en page pour l'impression : paysage, ajusté à une page ----
        sheet.set_landscape()
        sheet.fit_to_pages(1, 0)  # 1 page de large, hauteur libre
        sheet.repeat_rows(0, 1)   # titre + en-tête répétés à chaque page

        workbook.close()
        data = buffer.getvalue()
        buffer.close()
        return data

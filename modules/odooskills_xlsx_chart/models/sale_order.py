import io

from odoo import models, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_export_lines_xlsx_chart(self):
        """Bouton d'en-tête : télécharge le rapport XLSX avec graphiques."""
        ids = ','.join(str(i) for i in self.ids)
        return {
            'type': 'ir.actions.act_url',
            'url': '/odooskills/export/sale_lines/xlsx_chart?order_ids=%s' % ids,
            'target': 'self',
        }

    def _aggregate_ca(self):
        """Agrège le CA HT des lignes par produit et par mois.

        Retourne deux listes de tuples triées prêtes à tracer :
        - par produit, décroissant, limité au top 10 ;
        - par mois, chronologique (clé 'AAAA-MM' → libellé 'MM/AAAA').
        """
        by_product = {}
        by_month = {}
        for order in self:
            month_key = order.date_order.strftime('%Y-%m') if order.date_order else _('Inconnu')
            for line in order.order_line.filtered(lambda l: not l.display_type):
                name = line.product_id.display_name or line.name
                by_product[name] = by_product.get(name, 0.0) + line.price_subtotal
                by_month[month_key] = by_month.get(month_key, 0.0) + line.price_subtotal

        products = sorted(by_product.items(), key=lambda kv: kv[1], reverse=True)[:10]
        months = sorted(by_month.items(), key=lambda kv: kv[0])
        # Libellé lisible 'MM/AAAA' pour les mois datés.
        months = [
            (('%s/%s' % (k[5:], k[:4])) if '-' in k else k, v)
            for k, v in months
        ]
        return products, months

    def _build_sale_lines_xlsx_chart(self):
        """Construit un classeur Excel avec graphiques natifs.

        Une feuille « Tableau de bord » porte trois graphiques — histogramme
        et camembert du CA par produit, courbe du CA par mois — alimentés par
        deux feuilles de données. Retourne les octets (`bytes`) du .xlsx.
        """
        import xlsxwriter  # vendored par Odoo

        products, months = self._aggregate_ca()

        buffer = io.BytesIO()
        workbook = xlsxwriter.Workbook(buffer, {'in_memory': True})

        title_fmt = workbook.add_format({
            'bold': True, 'font_size': 14, 'font_color': '#FFFFFF',
            'bg_color': '#1D6F42', 'align': 'center', 'valign': 'vcenter',
        })
        header_fmt = workbook.add_format({
            'bold': True, 'font_color': '#FFFFFF', 'bg_color': '#2E7D54',
            'border': 1, 'align': 'center', 'valign': 'vcenter',
        })
        text_fmt = workbook.add_format({'border': 1})
        money_fmt = workbook.add_format({'num_format': '#,##0.00\\ €', 'border': 1})

        # Feuille tableau de bord créée EN PREMIER → onglet en tête. Les
        # graphiques référencent des plages par leur nom de feuille ; les
        # feuilles de données peuvent être créées après.
        dashboard = workbook.add_worksheet(_('Tableau de bord'))
        dashboard.activate()

        prod_sheet_name = _('CA par produit')
        month_sheet_name = _('CA par mois')
        n_prod = self._write_data_sheet(
            workbook.add_worksheet(prod_sheet_name), prod_sheet_name,
            _('Produit'), products, title_fmt, header_fmt, text_fmt, money_fmt,
        )
        n_month = self._write_data_sheet(
            workbook.add_worksheet(month_sheet_name), month_sheet_name,
            _('Mois'), months, title_fmt, header_fmt, text_fmt, money_fmt,
        )

        # --- Graphique 1 : histogramme du CA par produit --------------------
        if n_prod:
            col_chart = workbook.add_chart({'type': 'column'})
            col_chart.add_series({
                'name': _('CA HT par produit'),
                'categories': [prod_sheet_name, 2, 0, n_prod + 1, 0],
                'values': [prod_sheet_name, 2, 1, n_prod + 1, 1],
                'data_labels': {'value': True, 'num_format': '#,##0\\ €'},
                'fill': {'color': '#1D6F42'},
            })
            col_chart.set_title({'name': _('CA HT par produit')})
            col_chart.set_legend({'none': True})
            col_chart.set_y_axis({'num_format': '#,##0\\ €'})
            col_chart.set_size({'width': 640, 'height': 380})
            dashboard.insert_chart('B2', col_chart)

            # --- Graphique 2 : camembert de répartition par produit ---------
            pie_chart = workbook.add_chart({'type': 'pie'})
            pie_chart.add_series({
                'name': _('Répartition du CA par produit'),
                'categories': [prod_sheet_name, 2, 0, n_prod + 1, 0],
                'values': [prod_sheet_name, 2, 1, n_prod + 1, 1],
                'data_labels': {'percentage': True},
            })
            pie_chart.set_title({'name': _('Répartition du CA par produit')})
            pie_chart.set_legend({'position': 'bottom'})
            pie_chart.set_size({'width': 640, 'height': 420})
            dashboard.insert_chart('B22', pie_chart)

        # --- Graphique 3 : courbe du CA par mois ----------------------------
        if n_month:
            line_chart = workbook.add_chart({'type': 'line'})
            line_chart.add_series({
                'name': _('CA HT par mois'),
                'categories': [month_sheet_name, 2, 0, n_month + 1, 0],
                'values': [month_sheet_name, 2, 1, n_month + 1, 1],
                'line': {'color': '#1D6F42', 'width': 2.25},
                'marker': {'type': 'circle', 'size': 6},
            })
            line_chart.set_title({'name': _('CA HT par mois')})
            line_chart.set_legend({'none': True})
            line_chart.set_y_axis({'num_format': '#,##0\\ €'})
            line_chart.set_size({'width': 640, 'height': 380})
            dashboard.insert_chart('K2', line_chart)

        workbook.close()
        data = buffer.getvalue()
        buffer.close()
        return data

    def _write_data_sheet(self, sheet, sheet_title, label, rows,
                          title_fmt, header_fmt, text_fmt, money_fmt):
        """Écrit une table à deux colonnes (libellé, CA HT). Renvoie le nb de lignes.

        Les données démarrent en ligne 3 (index 2) pour laisser un titre fusionné
        en ligne 1 et l'en-tête en ligne 2 — les graphiques pointent donc sur la
        plage A3:B(n+2).
        """
        sheet.merge_range(0, 0, 0, 1, sheet_title, title_fmt)
        sheet.set_row(0, 22)
        sheet.write(1, 0, label, header_fmt)
        sheet.write(1, 1, _('CA HT'), header_fmt)
        row = 2
        for name, amount in rows:
            sheet.write(row, 0, name, text_fmt)
            sheet.write_number(row, 1, amount, money_fmt)
            row += 1
        sheet.set_column(0, 0, 32)
        sheet.set_column(1, 1, 16)
        return len(rows)

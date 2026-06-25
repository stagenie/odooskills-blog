import io

from odoo import models, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_export_lines_xlsx(self):
        """Bouton d'en-tête : redirige vers la route de téléchargement du rapport XLSX."""
        ids = ','.join(str(i) for i in self.ids)
        return {
            'type': 'ir.actions.act_url',
            'url': '/odooskills/export/sale_lines/xlsx?order_ids=%s' % ids,
            'target': 'self',
        }

    def _build_sale_lines_xlsx(self):
        """Construit le classeur Excel des lignes des commandes du recordset.

        Retourne les octets (`bytes`) du fichier .xlsx — utilisable depuis un
        controller HTTP comme depuis un test, sans dépendance OCA.
        """
        import xlsxwriter  # vendored par Odoo

        buffer = io.BytesIO()
        workbook = xlsxwriter.Workbook(buffer, {'in_memory': True})
        sheet = workbook.add_worksheet(_('Lignes de vente'))

        header_fmt = workbook.add_format({
            'bold': True, 'bg_color': '#1D6F42', 'font_color': '#FFFFFF', 'border': 1,
        })
        money_fmt = workbook.add_format({'num_format': '#,##0.00'})

        headers = [
            _('Commande'), _('Client'), _('Produit'),
            _('Quantité'), _('Prix unitaire'), _('Total HT'),
        ]
        for col, label in enumerate(headers):
            sheet.write(0, col, label, header_fmt)
        widths = [len(h) for h in headers]

        row = 1
        for order in self:
            for line in order.order_line.filtered(lambda l: not l.display_type):
                cells = [
                    order.name,
                    order.partner_id.display_name,
                    line.product_id.display_name or line.name,
                    line.product_uom_qty,
                    line.price_unit,
                    line.price_subtotal,
                ]
                sheet.write(row, 0, cells[0])
                sheet.write(row, 1, cells[1])
                sheet.write(row, 2, cells[2])
                sheet.write(row, 3, cells[3])
                sheet.write(row, 4, cells[4], money_fmt)
                sheet.write(row, 5, cells[5], money_fmt)
                for col, value in enumerate(cells):
                    widths[col] = max(widths[col], len(str(value)))
                row += 1

        for col, width in enumerate(widths):
            sheet.set_column(col, col, min(width + 2, 50))

        workbook.close()
        data = buffer.getvalue()
        buffer.close()
        return data

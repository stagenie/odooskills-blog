from odoo import models


class ReportSalesSummary(models.AbstractModel):
    # _name = report.<report_name de l'action> : c'est ce modèle que le moteur
    # appelle pour fournir les données du template.
    _name = 'report.odooskills_report_dynamic_demo.report_sales_summary'
    _description = "Synthèse des ventes par catégorie"

    def _get_report_values(self, docids, data=None):
        docs = self.env['sale.order'].browse(docids)

        # Agrégation SQL : somme des quantités et des montants par produit.
        groups = self.env['sale.order.line']._read_group(
            domain=[('order_id', 'in', docs.ids), ('display_type', '=', False)],
            groupby=['product_id'],
            aggregates=['product_uom_qty:sum', 'price_subtotal:sum'],
        )

        # Repli par catégorie de produit (dictionnaire simple, sans import).
        by_category = {}
        for product, qty, subtotal in groups:
            name = product.categ_id.display_name or "Sans catégorie"
            bucket = by_category.setdefault(name, {'qty': 0.0, 'subtotal': 0.0})
            bucket['qty'] += qty
            bucket['subtotal'] += subtotal

        summary = [
            {'category': name, 'qty': vals['qty'], 'subtotal': vals['subtotal']}
            for name, vals in sorted(by_category.items())
        ]
        grand_total = sum(row['subtotal'] for row in summary)

        return {
            'doc_ids': docids,
            'doc_model': 'sale.order',
            'docs': docs,
            'summary': summary,
            'grand_total': grand_total,
        }

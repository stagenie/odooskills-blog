from odoo.http import Controller, request, route, content_disposition


class OdooSkillsXlsxBulkExport(Controller):

    @route('/odooskills/export/sales/xlsx_bulk', type='http', auth='user', readonly=True)
    def export_sales_xlsx_bulk(self, **kw):
        content = request.env['sale.order']._build_sales_xlsx_bulk()
        headers = [
            ('Content-Type',
             'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
            ('Content-Disposition', content_disposition('rapport_ventes_synthese.xlsx')),
        ]
        return request.make_response(content, headers)

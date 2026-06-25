from odoo.http import Controller, request, route, content_disposition


class OdooSkillsXlsxChartExport(Controller):

    @route('/odooskills/export/sale_lines/xlsx_chart', type='http', auth='user', readonly=True)
    def export_sale_lines_xlsx_chart(self, order_ids=None, **kw):
        ids = [int(x) for x in (order_ids or '').split(',') if x.strip().isdigit()]
        orders = request.env['sale.order'].browse(ids).exists()
        content = orders._build_sale_lines_xlsx_chart()
        headers = [
            ('Content-Type',
             'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
            ('Content-Disposition', content_disposition('rapport_ventes_graphiques.xlsx')),
        ]
        return request.make_response(content, headers)

from odoo.http import Controller, request, route, content_disposition


class OdooSkillsXlsxExport(Controller):

    @route('/odooskills/export/sale_lines/xlsx', type='http', auth='user', readonly=True)
    def export_sale_lines_xlsx(self, order_ids=None, **kw):
        ids = [int(x) for x in (order_ids or '').split(',') if x.strip().isdigit()]
        orders = request.env['sale.order'].browse(ids).exists()
        content = orders._build_sale_lines_xlsx()
        headers = [
            ('Content-Type',
             'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
            ('Content-Disposition', content_disposition('rapport_ventes.xlsx')),
        ]
        return request.make_response(content, headers)

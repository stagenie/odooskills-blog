from odoo import http
from odoo.http import request


class CodeClientController(http.Controller):

    @http.route('/oski/code-client/<int:partner_id>', type='http', auth='user', methods=['GET'])
    def lire_code(self, partner_id):
        partner = request.env['res.partner'].browse(partner_id).exists()
        if not partner:
            raise request.not_found()
        return request.make_json_response({
            'id': partner.id,
            'nom': partner.name,
            'code': partner.oski_code or None,
        })

    @http.route('/oski/code-client/generer', type='jsonrpc', auth='user')
    def generer_code(self, partner_id):
        partner = request.env['res.partner'].browse(partner_id)
        partner.action_oski_generer_code()
        return {'code': partner.oski_code}

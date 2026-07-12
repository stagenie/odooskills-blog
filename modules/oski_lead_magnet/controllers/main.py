from odoo import http
from odoo.http import request


class OskiLeadController(http.Controller):

    @http.route('/oski/lead/subscribe', type='json', auth='public',
                methods=['POST'], website=True, csrf=False)
    def subscribe(self, email=None, consent=False, source='popup', blog_post_id=None):
        post = None
        if blog_post_id:
            post = request.env['blog.post'].sudo().browse(int(blog_post_id)).exists()
        return request.env['oski.lead.capture'].sudo()._oski_capture_lead(
            email, bool(consent), source, post)

from odoo import http
from odoo.http import request


class OskiLeadController(http.Controller):

    @http.route('/oski/lead/subscribe', type='json', auth='public',
                methods=['POST'], website=True, csrf=False)
    def subscribe(self, email=None, consent=False, source='popup', blog_post_id=None):
        post = None
        if blog_post_id is not None:
            try:
                pid = int(blog_post_id)
            except (TypeError, ValueError):
                pid = 0
            if pid:
                post = request.env['blog.post'].sudo().browse(pid).exists()
                if post and not post.website_published:
                    post = None
        consent_bool = consent in (True, 'true', 'True', '1', 1, 'on', 'yes')
        return request.env['oski.lead.capture'].sudo()._oski_capture_lead(
            email, consent_bool, source, post,
            client_ip=request.httprequest.remote_addr)

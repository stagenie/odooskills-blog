from odoo import http
from odoo.http import request


class OskiLeadController(http.Controller):

    @http.route('/oski/lead/subscribe', type='jsonrpc', auth='public',
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
        res = request.env['oski.lead.capture'].sudo()._oski_capture_lead(
            email, consent_bool, source, post,
            client_ip=request.httprequest.remote_addr)
        if res.get('ok'):
            # Mémorise l'adresse pour l'écran de confirmation : /oski/lead/consent
            # ne prend AUCUN email en paramètre, sinon n'importe qui pourrait
            # inscrire n'importe quelle adresse à la liste.
            request.session['oski_lead_email'] = (email or '').strip().lower()
        return res

    @http.route('/oski/lead/consent', type='jsonrpc', auth='public',
                methods=['POST'], website=True, csrf=False)
    def grant_consent(self):
        """Consentement donné après le téléchargement, sur l'adresse de la session.

        Aucun paramètre : l'adresse vient de la session posée par subscribe().
        """
        email = request.session.get('oski_lead_email')
        if not email:
            return {'ok': False, 'error': 'no_session'}
        ok = request.env['oski.lead.capture'].sudo()._oski_grant_consent(email)
        return {'ok': bool(ok), 'error': None if ok else 'invalid'}

    @http.route('/oski/offer/grid', type='jsonrpc', auth='public',
                methods=['POST'], website=True, csrf=False)
    def offer_grid(self):
        Offer = request.env['oski.welcome.offer'].sudo()
        return {'percent': Offer._welcome_percent(), 'rows': Offer._price_grid()}

    @http.route('/oski/offer/<string:token>', type='http', auth='public',
                website=True, sitemap=False)
    def offer_landing(self, token, **kw):
        offer = request.env['oski.welcome.offer'].sudo().search(
            [('token', '=', token)], limit=1)
        if not offer:
            return request.not_found()
        return request.render('oski_lead_magnet.offer_page', {'offer': offer})

    @http.route('/oski/offer/<string:token>/start', type='http', auth='public',
                website=True, sitemap=False, methods=['POST'])
    def offer_landing_start(self, token, **kw):
        offer = request.env['oski.welcome.offer'].sudo().search(
            [('token', '=', token)], limit=1)
        if not offer:
            return request.not_found()
        offer.activate()
        return request.render('oski_lead_magnet.offer_page', {'offer': offer})

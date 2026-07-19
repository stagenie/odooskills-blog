import logging

from odoo import api, models

_logger = logging.getLogger(__name__)


class OskiLeadCapture(models.AbstractModel):
    _inherit = 'oski.lead.capture'

    @api.model
    def _oski_capture_lead(self, email, consent, source, blog_post=None,
                           client_ip=None):
        result = super()._oski_capture_lead(
            email, consent, source, blog_post, client_ip=client_ip)
        if result.get('ok') and result.get('pdf_url') and blog_post:
            self._oski_send_pdf_mail(email, blog_post, result['pdf_url'])
        return result

    @api.model
    def _oski_send_pdf_mail(self, email, blog_post, pdf_url):
        """Copie par email du lien de téléchargement. Le téléchargement
        immédiat reste la voie principale : un échec d'envoi ne doit jamais
        casser la livraison."""
        template = self.env.ref('oski_article_pdf.mail_pdf_delivery',
                                raise_if_not_found=False)
        if not template:
            return
        base = self.env['ir.config_parameter'].sudo().get_param(
            'web.base.url', 'https://odooskills.com').rstrip('/')
        absolute = pdf_url if pdf_url.startswith('http') else base + pdf_url
        try:
            template.sudo().with_context(pdf_url=absolute).send_mail(
                blog_post.id, force_send=True,
                email_values={'email_to': email})
        except Exception:
            _logger.exception("Échec d'envoi du guide PDF à %s", email)

import re

from odoo import api, models
from odoo.exceptions import UserError

# src="/…" ou href='/…' mais PAS "//" (protocol-relative) ni "#ancre"
# Capture le guillemet utilisé (simple ou double) pour le réémettre tel quel.
_REL_URL_RE = re.compile(r'(\s(?:src|href)=)(["\'])(/(?!/))')


class OskiPdfRenderer(models.AbstractModel):
    _name = 'oski.pdf.renderer'
    _description = "Rendu HTML → PDF (WeasyPrint)"

    @api.model
    def _base_url(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param(
            'web.base.url')
        if not base_url:
            raise UserError(
                "Le paramètre système « web.base.url » n'est pas configuré. "
                "Il doit être renseigné pour générer un guide PDF."
            )
        return base_url.rstrip('/')

    @api.model
    def _absolutize(self, html):
        """WeasyPrint n'a pas de contexte de session : les URL relatives
        doivent être résolues avant le rendu."""
        base_url = self._base_url()
        return _REL_URL_RE.sub(
            lambda m: '%s%s%s%s' % (m.group(1), m.group(2), base_url,
                                     m.group(3)),
            html or '')

    @api.model
    def _render_pdf(self, html):
        """HTML complet → octets PDF."""
        try:
            from weasyprint import HTML
        except ImportError as err:
            raise UserError(
                "WeasyPrint n'est pas installé sur ce serveur. "
                "Installer les dépendances système (libpango-1.0-0, "
                "libpangoft2-1.0-0, libcairo2, libgdk-pixbuf-2.0-0) puis "
                "« pip install weasyprint==68.1 » dans le venv Odoo."
            ) from err
        return HTML(string=self._absolutize(html),
                    base_url=self._base_url()).write_pdf()

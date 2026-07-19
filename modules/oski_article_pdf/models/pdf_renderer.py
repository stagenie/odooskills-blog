import logging
import re

from odoo import api, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

# src="/…" ou href="/…" mais PAS "//" (protocol-relative) ni "#ancre"
_REL_URL_RE = re.compile(r'(\s(?:src|href)=")(/(?!/))')


class OskiPdfRenderer(models.AbstractModel):
    _name = 'oski.pdf.renderer'
    _description = "Rendu HTML → PDF (WeasyPrint)"

    @api.model
    def _base_url(self):
        return self.env['ir.config_parameter'].sudo().get_param(
            'web.base.url', 'https://odooskills.com').rstrip('/')

    @api.model
    def _absolutize(self, html):
        """WeasyPrint n'a pas de contexte de session : les URL relatives
        doivent être résolues avant le rendu."""
        return _REL_URL_RE.sub(r'\g<1>%s/' % self._base_url(), html or '')

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

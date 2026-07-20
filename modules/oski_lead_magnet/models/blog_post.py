import json
import re

from odoo import fields, models

# cover_properties stocke la couverture sous la forme CSS `url("/web/image/…")`.
_COVER_URL_RE = re.compile(r'url\((["\']?)(?P<url>.+?)\1\)')


class OskiPdfSeries(models.Model):
    _name = 'oski.pdf.series'
    _description = "PDF combiné d'une série d'articles"

    name = fields.Char(required=True)
    attachment_id = fields.Many2one('ir.attachment', string="PDF combiné", required=True)


class BlogPost(models.Model):
    _inherit = 'blog.post'

    oski_pdf_attachment_id = fields.Many2one(
        'ir.attachment', string="PDF de l'article",
        help="PDF soigné proposé au téléchargement (gate email).")
    oski_pdf_series_id = fields.Many2one(
        'oski.pdf.series', string="Série (PDF combiné)",
        help="Si renseigné, le PDF de la série prime sur celui de l'article.")

    def _oski_pdf_attachment(self):
        self.ensure_one()
        return self.oski_pdf_series_id.attachment_id or self.oski_pdf_attachment_id

    def _oski_pdf_download_url(self):
        self.ensure_one()
        att = self._oski_pdf_attachment()
        if not att:
            return False
        return '/web/content/%s?download=true' % att.id

    def _oski_pdf_gated_url(self):
        self.ensure_one()
        att = self._oski_pdf_attachment()
        if not att:
            return False
        token = att.access_token or att.sudo().generate_access_token()[0]
        return '/web/content/%s?access_token=%s&download=true' % (att.id, token)

    def _oski_cover_url(self):
        """URL de la couverture de l'article, pour habiller le modal.

        La couverture vit dans `cover_properties`, un JSON dont la clé
        `background-image` vaut soit `none`, soit une valeur CSS
        `url("/web/image/…")`. Renvoie False si l'article n'a pas de
        couverture : le modal retombe alors sur son dégradé.
        """
        self.ensure_one()
        try:
            props = json.loads(self.cover_properties or '{}')
        except (TypeError, ValueError):
            return False
        raw = (props.get('background-image') or '').strip()
        if not raw or raw == 'none':
            return False
        match = _COVER_URL_RE.search(raw)
        if not match:
            return False
        url = match.group('url').strip()
        # Une couverture externe (autre domaine) est ignorée : le modal ne doit
        # pas dépendre d'un hôte tiers pour s'afficher.
        return url if url.startswith('/') else False

from odoo import fields, models


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

    def _oski_pdf_download_url(self):
        self.ensure_one()
        att = self.oski_pdf_series_id.attachment_id or self.oski_pdf_attachment_id
        if not att:
            return False
        return '/web/content/%s?download=true' % att.id

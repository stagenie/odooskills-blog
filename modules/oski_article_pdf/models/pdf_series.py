import base64
import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class OskiPdfSeries(models.Model):
    _inherit = 'oski.pdf.series'

    post_ids = fields.One2many('blog.post', 'oski_pdf_series_id', string="Articles")
    subtitle = fields.Char(string="Sous-titre")
    generated_on = fields.Datetime(string="Généré le", readonly=True)

    def _oski_ordered_posts(self):
        self.ensure_one()
        return self.post_ids.sorted(
            key=lambda p: (p.oski_series_seq, p.post_date or fields.Datetime.now()))

    def _oski_generate_pdf(self):
        """Un SEUL rendu QWeb sur tous les articles ordonnés : pagination
        continue et sommaire cohérent (pas une concaténation de PDF)."""
        self.ensure_one()
        posts = self._oski_ordered_posts()
        if not posts:
            return self.env['ir.attachment']
        html = self.env['ir.qweb']._render('oski_article_pdf.guide_document', {
            'posts': posts,
            'title': self.name or '',
            'subtitle': self.subtitle or '',
            'meta': '%s articles · odooskills.com' % len(posts),
            'is_series': True,
        })
        pdf_bytes = self.env['oski.pdf.renderer']._render_pdf(str(html))

        old = self.attachment_id
        attachment = self.env['ir.attachment'].sudo().create({
            'name': 'odooskills-serie-%s.pdf' % self.id,
            'datas': base64.b64encode(pdf_bytes),
            'mimetype': 'application/pdf',
            'res_model': 'oski.pdf.series',
            'res_id': self.id,
            'public': False,
        })
        now = fields.Datetime.now()
        self.write({'attachment_id': attachment.id,
                    'generated_on': now})
        for post in posts:
            post.write({
                'oski_pdf_generated_on': now,
                'oski_pdf_source_hash': post._oski_source_hash(),
            })
        if old:
            old.sudo().unlink()
        _logger.info("Guide PDF de série %s généré (%s articles, %s o)",
                     self.id, len(posts), len(pdf_bytes))
        return attachment

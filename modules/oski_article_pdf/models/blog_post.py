import base64
import hashlib
import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class BlogPost(models.Model):
    _inherit = 'blog.post'

    oski_series_seq = fields.Integer(
        string="Ordre dans la série", default=10,
        help="Ordre de lecture dans le guide combiné. La date de publication "
             "ne reflète pas toujours l'ordre pédagogique.")
    oski_pdf_generated_on = fields.Datetime(string="Guide PDF généré le", readonly=True)
    oski_pdf_source_hash = fields.Char(string="Empreinte source", readonly=True)
    oski_pdf_stale = fields.Boolean(
        string="Guide PDF périmé", compute='_compute_oski_pdf_stale')

    def _oski_source_hash(self):
        """Empreinte du contenu qui alimente le PDF."""
        self.ensure_one()
        raw = '%s|%s|%s' % (
            self.name or '', self.subtitle or '', str(self.content or ''))
        return hashlib.sha256(raw.encode('utf-8')).hexdigest()

    @api.depends('name', 'subtitle', 'content', 'oski_pdf_source_hash',
                 'oski_pdf_generated_on')
    def _compute_oski_pdf_stale(self):
        for post in self:
            if not post.oski_pdf_generated_on or not post.oski_pdf_source_hash:
                post.oski_pdf_stale = True
            else:
                post.oski_pdf_stale = (
                    post.oski_pdf_source_hash != post._oski_source_hash())

    def _oski_pdf_filename(self):
        self.ensure_one()
        slug = (self.name or 'guide').lower()
        slug = ''.join(c if c.isalnum() else '-' for c in slug).strip('-')
        while '--' in slug:
            slug = slug.replace('--', '-')
        return 'odooskills-%s.pdf' % slug[:60]

    def _oski_generate_pdf(self):
        """Rend le guide PDF de CET article et l'attache."""
        self.ensure_one()
        html = self.env['ir.qweb']._render('oski_article_pdf.guide_document', {
            'posts': self,
            'title': self.name or '',
            'subtitle': self.subtitle or '',
            'meta': '%s · %s · odooskills.com' % (
                self.blog_id.name or '',
                fields.Date.to_string(self.post_date) if self.post_date else ''),
            'is_series': False,
        })
        pdf_bytes = self.env['oski.pdf.renderer']._render_pdf(str(html))

        old = self.oski_pdf_attachment_id
        attachment = self.env['ir.attachment'].sudo().create({
            'name': self._oski_pdf_filename(),
            'datas': base64.b64encode(pdf_bytes),
            'mimetype': 'application/pdf',
            'res_model': 'blog.post',
            'res_id': self.id,
            'public': False,
        })
        self.write({
            'oski_pdf_attachment_id': attachment.id,
            'oski_pdf_generated_on': fields.Datetime.now(),
            'oski_pdf_source_hash': self._oski_source_hash(),
        })
        if old:
            old.sudo().unlink()
        _logger.info("Guide PDF généré pour l'article %s (%s o)", self.id, len(pdf_bytes))
        return attachment

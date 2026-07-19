import hashlib

from odoo import api, fields, models


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

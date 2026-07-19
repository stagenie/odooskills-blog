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

    # champs dont la modification rend le PDF obsolète
    _OSKI_PDF_SOURCE_FIELDS = {'name', 'subtitle', 'content', 'oski_pdf_series_id',
                               'oski_series_seq'}

    def write(self, vals):
        res = super().write(vals)
        becomes_published = vals.get('is_published') is True
        content_touched = bool(self._OSKI_PDF_SOURCE_FIELDS & set(vals))
        if becomes_published or content_touched:
            if any(p.is_published for p in self):
                self._oski_trigger_generation()
        return res

    def _oski_trigger_generation(self):
        """Planifie la génération hors requête HTTP."""
        cron = self.env.ref('oski_article_pdf.cron_generate_pdf',
                            raise_if_not_found=False)
        if cron:
            cron.sudo()._trigger()

    @api.model_create_multi
    def create(self, vals_list):
        posts = super().create(vals_list)
        if any(post.is_published for post in posts):
            posts._oski_trigger_generation()
        return posts

    @api.model
    def _cron_generate_pending(self):
        """Génère les guides manquants ou périmés, les plus lus d'abord.

        Une série est générée au plus une fois par vague : le rendu combiné
        (WeasyPrint sur tous les articles de la série) est coûteux, et le
        générer efface la péremption de TOUS ses membres. `pending` est
        calculé une seule fois en amont et n'est jamais réévalué pendant la
        boucle : sans garde explicite, les membres suivants de la même
        série resteraient dans la liste et provoqueraient un rendu par
        membre périmé au lieu d'un seul rendu pour la série entière.
        """
        pending = self.search([('is_published', '=', True)]).filtered(
            lambda p: p.oski_pdf_stale)
        pending = pending.sorted(key=lambda p: p.visits or 0, reverse=True)
        done_series_ids = set()
        for post in pending:
            try:
                series = post.oski_pdf_series_id
                if series:
                    if series.id in done_series_ids:
                        continue
                    done_series_ids.add(series.id)
                    series._oski_generate_pdf()
                else:
                    post._oski_generate_pdf()
                self.env.cr.commit()
            except Exception:
                self.env.cr.rollback()
                _logger.exception(
                    "Échec de génération du guide PDF pour l'article %s", post.id)

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
        """Articles publiés de la série, dans l'ordre de lecture.

        Les brouillons ne doivent JAMAIS entrer dans le rendu combiné : le
        cron tourne sans règle d'accès website (contexte interne), donc sans
        ce filtre un brouillon attaché à la série serait rendu et livré à
        n'importe quel lecteur qui laisse son email sur le premier article
        publié."""
        self.ensure_one()
        return self.post_ids.filtered('is_published').sorted(
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

        # Régénération EN PLACE, même exigence que pour l'article seul : un
        # lien tokenisé de série a pu être livré par email. On réécrit le
        # contenu sur l'attachement existant (le champ est required, donc il
        # y en a toujours un) plutôt que d'en créer un nouveau et de
        # supprimer l'ancien, ce qui casserait ce lien. Cela supprime aussi
        # la course entre le cron et l'action groupée qui pouvaient chacun
        # supprimer la pièce jointe de l'autre.
        attachment = self.attachment_id
        vals = {
            'name': 'odooskills-serie-%s.pdf' % self.id,
            'datas': base64.b64encode(pdf_bytes),
            'mimetype': 'application/pdf',
            'res_model': 'oski.pdf.series',
            'res_id': self.id,
            'public': False,
        }
        if attachment:
            attachment.sudo().write(vals)
        else:
            attachment = self.env['ir.attachment'].sudo().create(vals)
        now = fields.Datetime.now()
        self.write({'attachment_id': attachment.id,
                    'generated_on': now})
        for post in posts:
            post.write({
                'oski_pdf_generated_on': now,
                'oski_pdf_source_hash': post._oski_source_hash(),
            })
        _logger.info("Guide PDF de série %s généré (%s articles, %s o)",
                     self.id, len(posts), len(pdf_bytes))
        return attachment

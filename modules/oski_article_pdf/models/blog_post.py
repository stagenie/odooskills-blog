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
    oski_pdf_generated_on = fields.Datetime(
        string="Guide PDF généré le", readonly=True, copy=False)
    oski_pdf_source_hash = fields.Char(
        string="Empreinte source", readonly=True, copy=False)
    # oski_pdf_attachment_id est défini dans oski_lead_magnet (module dont
    # celui-ci dépend) sans copy=False : sans cette surcharge, dupliquer un
    # article copierait la référence à l'attachement PDF de l'original. Or
    # la régénération réécrit désormais EN PLACE (même id de pièce jointe,
    # même res_id réécrit) pour préserver les liens tokenisés déjà envoyés
    # par email : régénérer le PDF du doublon écraserait alors silencieusement
    # le PDF de l'ORIGINAL.
    oski_pdf_attachment_id = fields.Many2one(copy=False)
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

        # Régénération EN PLACE : un lecteur a pu recevoir par email un lien
        # tokenisé pointant sur cette pièce jointe précise
        # (/web/content/<id>?access_token=<token>). La remplacer par une
        # nouvelle pièce jointe (id différent) casserait tous les liens déjà
        # livrés. On réécrit donc le contenu sur l'attachement existant ; on
        # ne crée un nouvel enregistrement que s'il n'y en avait aucun.
        attachment = self.oski_pdf_attachment_id
        vals = {
            'name': self._oski_pdf_filename(),
            'datas': base64.b64encode(pdf_bytes),
            'mimetype': 'application/pdf',
            'res_model': 'blog.post',
            'res_id': self.id,
            'public': False,
        }
        if attachment:
            attachment.sudo().write(vals)
        else:
            attachment = self.env['ir.attachment'].sudo().create(vals)
        self.write({
            'oski_pdf_attachment_id': attachment.id,
            'oski_pdf_generated_on': fields.Datetime.now(),
            'oski_pdf_source_hash': self._oski_source_hash(),
        })
        _logger.info("Guide PDF généré pour l'article %s (%s o)", self.id, len(pdf_bytes))
        return attachment

    # champs dont la modification rend le PDF obsolète
    _OSKI_PDF_SOURCE_FIELDS = {'name', 'subtitle', 'content', 'oski_pdf_series_id',
                               'oski_series_seq'}
    # sous-ensemble de _OSKI_PDF_SOURCE_FIELDS qui touche la STRUCTURE d'une
    # série (et non son contenu texte) : _oski_source_hash() ne les hache
    # jamais, donc les modifier déclenche le cron sans jamais rendre le hash
    # périmé. Sans invalidation explicite, attacher/réordonner/détacher un
    # article ne produit aucune régénération réelle.
    _OSKI_PDF_STRUCTURE_FIELDS = {'oski_pdf_series_id', 'oski_series_seq'}

    def write(self, vals):
        structure_touched = bool(self._OSKI_PDF_STRUCTURE_FIELDS & set(vals))
        old_series = (self.mapped('oski_pdf_series_id') if structure_touched
                      else self.env['oski.pdf.series'])
        # un article rétracté (is_published -> False) qui appartient à une
        # série n'est ni un champ de STRUCTURE ni de CONTENU au sens de
        # _OSKI_PDF_STRUCTURE_FIELDS / _OSKI_PDF_SOURCE_FIELDS : sans ce
        # traitement dédié, aucun hash n'est jamais effacé et le PDF combiné
        # continue de diffuser indéfiniment le contenu rétracté aux
        # lecteurs qui capturent sur n'importe quel autre membre de la
        # série. La série est capturée AVANT le write car is_published ne
        # change jamais oski_pdf_series_id, donc l'ordre n'a pas
        # d'importance ici, mais on reste cohérent avec le traitement des
        # champs de structure ci-dessus.
        unpublished_series = (self.mapped('oski_pdf_series_id')
                              if vals.get('is_published') is False
                              else self.env['oski.pdf.series'])
        res = super().write(vals)
        becomes_published = vals.get('is_published') is True
        content_touched = bool(self._OSKI_PDF_SOURCE_FIELDS & set(vals))
        if structure_touched:
            new_series = self.mapped('oski_pdf_series_id')
            affected_posts = (self | old_series.mapped('post_ids')
                              | new_series.mapped('post_ids'))
            affected_posts.write({'oski_pdf_source_hash': False})
        if unpublished_series:
            unpublished_series.mapped('post_ids').write(
                {'oski_pdf_source_hash': False})
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

    def action_oski_generate_pdf(self):
        """Action groupée : vague de rattrapage, les plus lus d'abord.

        Même piège que `_cron_generate_pending` (Tâche 7) : si plusieurs
        articles sélectionnés appartiennent à la même série, il ne faut
        déclencher le rendu combiné qu'UNE SEULE fois pour cette série,
        pas une fois par membre sélectionné.
        """
        targets = self.filtered('is_published').sorted(
            key=lambda p: p.visits or 0, reverse=True)
        done_series_ids = set()
        for post in targets:
            series = post.oski_pdf_series_id
            if series:
                if series.id in done_series_ids:
                    continue
                done_series_ids.add(series.id)
                series._oski_generate_pdf()
            else:
                post._oski_generate_pdf()
        return True

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

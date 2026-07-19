import base64
from unittest.mock import patch

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestPublishTrigger(TransactionCase):
    def setUp(self):
        super().setUp()
        self.blog = self.env['blog.blog'].create({'name': 'Développement Odoo'})

    def _make(self, published):
        return self.env['blog.post'].create({
            'name': 'Article', 'blog_id': self.blog.id,
            'content': '<p>x</p>', 'is_published': published})

    def test_publishing_triggers_cron(self):
        post = self._make(False)
        with patch('odoo.addons.base.models.ir_cron.IrCron._trigger') as trig:
            post.is_published = True
            self.assertTrue(trig.called, "la publication doit déclencher le cron")

    def test_unpublishing_does_not_trigger(self):
        post = self._make(True)
        with patch('odoo.addons.base.models.ir_cron.IrCron._trigger') as trig:
            post.is_published = False
            self.assertFalse(trig.called)

    def test_editing_published_post_triggers(self):
        post = self._make(True)
        with patch('odoo.addons.base.models.ir_cron.IrCron._trigger') as trig:
            post.content = '<p>réécrit</p>'
            self.assertTrue(trig.called)

    def test_cron_generates_missing_pdf(self):
        post = self._make(True)
        self.assertTrue(post.oski_pdf_stale)
        # _cron_generate_pending() commite volontairement après chaque article
        # (isolation d'une vague de rattrapage réelle) — TransactionCase interdit
        # tout commit/rollback sur le curseur de test. On neutralise ici les
        # deux méthodes en no-op pour CE test uniquement : le code de
        # production continue réellement d'appeler cr.commit()/rollback(), on
        # masque juste leur effet de bord pendant l'appel. Ne pas "corriger"
        # en retirant le commit()/rollback() de blog_post.py.
        with patch.object(self.cr, 'commit', lambda: None), \
             patch.object(self.cr, 'rollback', lambda: None):
            self.env['blog.post']._cron_generate_pending()
        self.assertTrue(post.oski_pdf_attachment_id)
        self.assertFalse(post.oski_pdf_stale)

    def test_cron_skips_unpublished(self):
        post = self._make(False)
        self.env['blog.post']._cron_generate_pending()
        self.assertFalse(post.oski_pdf_attachment_id)

    def test_cron_generates_series_once_per_pass(self):
        # Une série avec plusieurs membres périmés ne doit être rendue
        # qu'UNE SEULE fois par vague de cron : le rendu combiné (WeasyPrint
        # sur tous les articles de la série) est l'opération la plus
        # coûteuse du module, et générer la série efface la péremption de
        # TOUS ses membres — les régénérer un par un est du gaspillage pur.
        placeholder = self.env['ir.attachment'].create({
            'name': 'p.pdf', 'datas': base64.b64encode(b'%PDF-old'),
            'mimetype': 'application/pdf'})
        series = self.env['oski.pdf.series'].create({
            'name': 'Série test', 'attachment_id': placeholder.id})
        posts = self.env['blog.post']
        for i in range(3):
            posts |= self.env['blog.post'].create({
                'name': 'Article série %s' % i, 'blog_id': self.blog.id,
                'content': '<p>%s</p>' % i, 'is_published': True,
                'oski_pdf_series_id': series.id, 'oski_series_seq': i * 10})
        for post in posts:
            self.assertTrue(post.oski_pdf_stale)
        with patch.object(self.cr, 'commit', lambda: None), \
             patch.object(self.cr, 'rollback', lambda: None), \
             patch(
                 'odoo.addons.oski_article_pdf.models.pdf_series.'
                 'OskiPdfSeries._oski_generate_pdf') as gen:
            self.env['blog.post']._cron_generate_pending()
        self.assertEqual(gen.call_count, 1,
                          "la série ne doit être générée qu'une seule fois "
                          "par vague de cron, quel que soit le nombre de "
                          "membres périmés")

    def test_create_published_triggers_cron(self):
        with patch('odoo.addons.base.models.ir_cron.IrCron._trigger') as trig:
            self._make(True)
            self.assertTrue(
                trig.called,
                "créer un article déjà publié doit déclencher le cron")

    def test_create_unpublished_does_not_trigger(self):
        with patch('odoo.addons.base.models.ir_cron.IrCron._trigger') as trig:
            self._make(False)
            self.assertFalse(trig.called)

    def test_cron_isolates_failures(self):
        ok = self._make(True)
        broken = self._make(True)
        original = type(self.env['blog.post'])._oski_generate_pdf

        def selective(self_post):
            if self_post.id == broken.id:
                raise ValueError("rendu impossible")
            return original(self_post)

        # blog.post a _order = 'id DESC' (website_blog/models/website_blog.py) :
        # `broken` (créé après `ok`, id plus grand) est donc traité EN PREMIER
        # par la boucle. Si le except de _cron_generate_pending() re-levait
        # l'exception au lieu de logguer et continuer, la boucle s'arrêterait
        # sur `broken` et n'atteindrait jamais `ok` : l'assertion ci-dessous
        # ne serait donc jamais vacuously vraie.
        # Même neutralisation de commit/rollback qu'au test précédent — voir
        # le commentaire de test_cron_generates_missing_pdf pour le pourquoi.
        with patch.object(type(self.env['blog.post']),
                          '_oski_generate_pdf', selective), \
             patch.object(self.cr, 'commit', lambda: None), \
             patch.object(self.cr, 'rollback', lambda: None):
            self.env['blog.post']._cron_generate_pending()
        self.assertTrue(ok.oski_pdf_attachment_id,
                        "un article en échec ne doit pas interrompre la vague")

    def test_cron_series_failure_dedup_holds(self):
        # Une série qui échoue doit être tentée une seule fois par vague, pas
        # N fois (une par membre périmé restant). Le dédup de `done_series_ids`
        # doit avoir lieu AVANT la tentative de rendu (ou dans un finally),
        # sinon une exception dans _oski_generate_pdf() empêche la marque
        # d'être enregistrée, et les membres suivants de la même série
        # réessayent la génération combinée au sein du même pass de cron.
        placeholder = self.env['ir.attachment'].create({
            'name': 'p.pdf', 'datas': base64.b64encode(b'%PDF-fail'),
            'mimetype': 'application/pdf'})
        series = self.env['oski.pdf.series'].create({
            'name': 'Série échouée', 'attachment_id': placeholder.id})
        posts = self.env['blog.post']
        for i in range(3):
            posts |= self.env['blog.post'].create({
                'name': 'Article série %s' % i, 'blog_id': self.blog.id,
                'content': '<p>%s</p>' % i, 'is_published': True,
                'oski_pdf_series_id': series.id, 'oski_series_seq': i * 10})
        for post in posts:
            self.assertTrue(post.oski_pdf_stale)
        # Patch la génération de la série pour lever une exception.
        # Neutralise aussi commit/rollback comme au test précédent.
        with patch.object(self.cr, 'commit', lambda: None), \
             patch.object(self.cr, 'rollback', lambda: None), \
             patch(
                 'odoo.addons.oski_article_pdf.models.pdf_series.'
                 'OskiPdfSeries._oski_generate_pdf',
                 side_effect=RuntimeError("template cassé")) as gen:
            self.env['blog.post']._cron_generate_pending()
        self.assertEqual(gen.call_count, 1,
                          "même avec une exception, la série ne doit être "
                          "générée qu'une seule fois par vague, pas une fois "
                          "par membre périmé (cela brûlerait de la CPU à tous "
                          "les passes de cron)")

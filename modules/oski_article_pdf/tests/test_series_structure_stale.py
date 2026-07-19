import base64

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestSeriesStructureStale(TransactionCase):
    """La péremption (`oski_pdf_stale`) ne dépend que d'un hash sur
    name|subtitle|content : elle est aveugle aux changements de STRUCTURE de
    série (attachement, réordonnancement, détachement), alors même que
    `write()` déclenche le cron pour ces champs. Ces tests prouvent que le
    hash est bien invalidé pour que le cron trouve réellement quelque chose
    à régénérer."""

    def setUp(self):
        super().setUp()
        self.blog = self.env['blog.blog'].create({'name': 'Développement Odoo'})

    def _series(self, name):
        placeholder = self.env['ir.attachment'].create({
            'name': 'p.pdf', 'datas': base64.b64encode(b'%PDF-old'),
            'mimetype': 'application/pdf'})
        return self.env['oski.pdf.series'].create({
            'name': name, 'attachment_id': placeholder.id})

    def _post(self, name, **vals):
        vals.setdefault('blog_id', self.blog.id)
        vals.setdefault('is_published', True)
        vals.setdefault('content', '<p>%s</p>' % name)
        vals['name'] = name
        return self.env['blog.post'].create(vals)

    def test_attach_to_series_marks_article_stale(self):
        series = self._series('Série A')
        post = self._post('Solo', oski_series_seq=10)
        post._oski_generate_pdf()
        self.assertFalse(post.oski_pdf_stale)

        post.write({'oski_pdf_series_id': series.id})

        self.assertTrue(
            post.oski_pdf_stale,
            "attacher un article déjà généré à une série doit le rendre "
            "périmé, sinon le cron se déclenche mais ne trouve rien à "
            "régénérer et le PDF de série ne contiendra jamais ce membre")

    def test_reorder_clears_hash_for_all_series_members(self):
        series = self._series('Série B')
        a = self._post('A', oski_series_seq=10, oski_pdf_series_id=series.id)
        b = self._post('B', oski_series_seq=20, oski_pdf_series_id=series.id)
        series._oski_generate_pdf()
        self.assertFalse(a.oski_pdf_stale)
        self.assertFalse(b.oski_pdf_stale)

        a.write({'oski_series_seq': 30})

        self.assertTrue(a.oski_pdf_stale)
        self.assertTrue(
            b.oski_pdf_stale,
            "réordonner un membre doit rendre périmés TOUS les membres de "
            "la série : le prochain cron doit régénérer le PDF combiné "
            "avec le nouvel ordre, pas seulement marquer le membre déplacé")

    def test_detach_from_series_clears_hash_and_regains_capture_gate(self):
        series = self._series('Série C')
        post = self._post(
            'Détaché', oski_series_seq=10, oski_pdf_series_id=series.id)
        series._oski_generate_pdf()
        self.assertFalse(post.oski_pdf_stale)
        self.assertFalse(
            post.oski_pdf_attachment_id,
            "un membre de série n'a pas son propre PDF individuel")

        post.write({'oski_pdf_series_id': False})

        self.assertTrue(
            post.oski_pdf_stale,
            "un article détaché doit redevenir périmé pour que le cron "
            "régénère SON PROPRE PDF individuel : sinon oski_pdf_stale "
            "reste False (hash intact hérité de la série) alors que "
            "oski_pdf_attachment_id reste vide pour toujours, ce qui "
            "supprime silencieusement sa porte de capture email")

import base64
from unittest.mock import patch

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestGenerateSeries(TransactionCase):
    def setUp(self):
        super().setUp()
        self.blog = self.env['blog.blog'].create({'name': 'Développement Odoo'})
        placeholder = self.env['ir.attachment'].create({
            'name': 'p.pdf', 'datas': base64.b64encode(b'%PDF-old'),
            'mimetype': 'application/pdf'})
        self.series = self.env['oski.pdf.series'].create({
            'name': 'Série Tech', 'attachment_id': placeholder.id})
        # créés dans le désordre exprès
        self.p2 = self._post('Deuxième', seq=20)
        self.p1 = self._post('Premier', seq=10)
        self.p3 = self._post('Troisième', seq=30)

    def _post(self, name, seq):
        return self.env['blog.post'].create({
            'name': name, 'blog_id': self.blog.id, 'is_published': True,
            'content': '<p>%s</p>' % name,
            'oski_pdf_series_id': self.series.id, 'oski_series_seq': seq})

    def test_post_ids_collects_members(self):
        self.assertEqual(len(self.series.post_ids), 3)

    def test_ordered_by_sequence_not_creation(self):
        self.assertEqual(
            self.series._oski_ordered_posts().mapped('name'),
            ['Premier', 'Deuxième', 'Troisième'])

    def test_ordered_posts_excludes_drafts(self):
        draft = self.env['blog.post'].create({
            'name': 'Brouillon', 'blog_id': self.blog.id, 'is_published': False,
            'content': '<p>Brouillon</p>',
            'oski_pdf_series_id': self.series.id, 'oski_series_seq': 5})
        self.assertNotIn(draft, self.series._oski_ordered_posts())
        self.assertEqual(
            self.series._oski_ordered_posts().mapped('name'),
            ['Premier', 'Deuxième', 'Troisième'])

    def test_draft_member_excluded_from_generated_pdf_content(self):
        """Un brouillon attaché à une série publiée ne doit jamais être
        rendu dans le PDF combiné : sinon publier le premier article de la
        série suffit à divulguer tout le contenu non publié aux lecteurs qui
        laissent leur email."""
        draft = self.env['blog.post'].create({
            'name': 'Brouillon secret', 'blog_id': self.blog.id,
            'is_published': False, 'content': '<p>Brouillon secret</p>',
            'oski_pdf_series_id': self.series.id, 'oski_series_seq': 5})
        captured = {}
        IrQweb = type(self.env['ir.qweb'])
        original_render = IrQweb._render

        def _capture(self_qweb, template, values=None, **kw):
            captured['posts'] = values.get('posts')
            return original_render(self_qweb, template, values, **kw)

        with patch.object(IrQweb, '_render', _capture):
            self.series._oski_generate_pdf()

        names = captured['posts'].mapped('name')
        self.assertNotIn('Brouillon secret', names,
                         "un brouillon ne doit jamais apparaître dans les données "
                         "passées au rendu QWeb du PDF de série")
        self.assertIn('Premier', names)

        self.assertFalse(
            draft.oski_pdf_generated_on,
            "un brouillon exclu du rendu ne doit pas être marqué comme généré")
        self.assertFalse(
            draft.oski_pdf_source_hash,
            "la péremption du brouillon ne doit pas être touchée par la "
            "génération de la série")

    def test_generates_single_pdf_with_all_articles(self):
        att = self.series._oski_generate_pdf()
        self.assertEqual(att.mimetype, 'application/pdf')
        self.assertTrue(base64.b64decode(att.datas).startswith(b'%PDF'))
        self.assertEqual(self.series.attachment_id, att)
        self.assertTrue(self.series.generated_on)

    def test_series_pdf_is_private(self):
        att = self.series._oski_generate_pdf()
        self.assertFalse(att.public)

    def test_member_post_resolves_to_series_pdf(self):
        att = self.series._oski_generate_pdf()
        self.assertEqual(self.p1._oski_pdf_attachment(), att)

    def test_all_members_marked_fresh_after_generation(self):
        self.series._oski_generate_pdf()
        for post in (self.p1, self.p2, self.p3):
            self.assertFalse(post.oski_pdf_stale, "%s doit être à jour" % post.name)
            self.assertTrue(post.oski_pdf_generated_on,
                             "%s doit avoir une date de génération" % post.name)

    def test_editing_one_member_only_marks_that_member_stale(self):
        self.series._oski_generate_pdf()
        self.p2.content = '<p>Deuxième réécrit</p>'
        self.assertTrue(self.p2.oski_pdf_stale)
        self.assertFalse(self.p1.oski_pdf_stale,
                          "l'empreinte d'un autre article ne doit pas contaminer p1")
        self.assertFalse(self.p3.oski_pdf_stale,
                          "l'empreinte d'un autre article ne doit pas contaminer p3")

    def test_regeneration_unlinks_old_attachment(self):
        placeholder_id = self.series.attachment_id.id
        att = self.series._oski_generate_pdf()
        self.assertFalse(
            self.env['ir.attachment'].browse(placeholder_id).exists(),
            "l'ancienne pièce jointe placeholder doit être supprimée")
        self.assertEqual(self.series.attachment_id, att)

    def test_empty_series_returns_empty_and_keeps_attachment(self):
        placeholder = self.env['ir.attachment'].create({
            'name': 'vide.pdf', 'datas': base64.b64encode(b'%PDF-vide'),
            'mimetype': 'application/pdf'})
        empty_series = self.env['oski.pdf.series'].create({
            'name': 'Série vide', 'attachment_id': placeholder.id})
        result = empty_series._oski_generate_pdf()
        self.assertFalse(result)
        self.assertEqual(empty_series.attachment_id, placeholder)
        self.assertTrue(placeholder.exists())

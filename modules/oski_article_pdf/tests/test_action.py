from unittest.mock import patch

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestAction(TransactionCase):
    def setUp(self):
        super().setUp()
        self.blog = self.env['blog.blog'].create({'name': 'Développement Odoo'})

    def _post(self, name, visits):
        return self.env['blog.post'].create({
            'name': name, 'blog_id': self.blog.id, 'is_published': True,
            'content': '<p>%s</p>' % name, 'visits': visits})

    def test_action_generates_for_all_selected(self):
        a, b = self._post('A', 10), self._post('B', 99)
        (a | b).action_oski_generate_pdf()
        self.assertTrue(a.oski_pdf_attachment_id)
        self.assertTrue(b.oski_pdf_attachment_id)

    def test_action_skips_unpublished(self):
        p = self._post('C', 5)
        p.is_published = False
        p.action_oski_generate_pdf()
        self.assertFalse(p.oski_pdf_attachment_id)

    def test_action_generates_series_once_for_multiple_selected_members(self):
        # Même piège qu'au cron de rattrapage (Tâche 7) : si l'utilisateur
        # sélectionne plusieurs articles d'une même série dans la vue liste
        # et lance l'action groupée, la série ne doit être rendue qu'UNE
        # SEULE fois — pas une fois par membre sélectionné, sans quoi le
        # rendu combiné coûteux (WeasyPrint sur tous les articles) serait
        # dupliqué N fois pour rien.
        series = self.env['oski.pdf.series'].create({
            'name': 'Série test',
            'attachment_id': self.env['ir.attachment'].create({
                'name': 'p.pdf', 'mimetype': 'application/pdf',
                'datas': b'',
            }).id,
        })
        posts = self.env['blog.post']
        for i in range(3):
            posts |= self._post('Article série %s' % i, visits=i)
            posts[-1].write({'oski_pdf_series_id': series.id,
                              'oski_series_seq': i * 10})
        with patch(
                'odoo.addons.oski_article_pdf.models.pdf_series.'
                'OskiPdfSeries._oski_generate_pdf') as gen:
            posts.action_oski_generate_pdf()
        self.assertEqual(
            gen.call_count, 1,
            "la série ne doit être générée qu'une seule fois par appel de "
            "l'action groupée, quel que soit le nombre de membres "
            "sélectionnés")

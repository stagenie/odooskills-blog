import base64

from odoo.tests import HttpCase, tagged


@tagged('post_install', '-at_install')
class TestGateCtaSeries(HttpCase):
    """Le libellé du CTA de téléchargement (gabarit oski_lead_magnet.pdf_gate_cta)
    doit s'adapter selon que l'article appartient à une série ou non. Ce
    comportement dépend de post_ids (One2many ajouté par oski_article_pdf sur
    oski.pdf.series) : il doit donc être porté par une vue héritée DANS ce
    module, pas par le module de base qui ignore post_ids."""

    def _attachment(self, name):
        return self.env['ir.attachment'].create({
            'name': name, 'datas': base64.b64encode(b'%PDF'),
            'mimetype': 'application/pdf', 'public': False})

    def test_series_wording_shows_article_count(self):
        blog = self.env['blog.blog'].create({'name': 'Développement Odoo'})
        series = self.env['oski.pdf.series'].create({
            'name': 'Série Tech', 'attachment_id': self._attachment('s.pdf').id})
        posts = self.env['blog.post']
        for i in range(3):
            posts |= self.env['blog.post'].create({
                'name': 'Article %s' % i, 'blog_id': blog.id,
                'content': '<p>x</p>', 'is_published': True,
                'oski_pdf_series_id': series.id, 'oski_series_seq': i * 10})
        post = posts[0]
        r = self.url_open('/blog/%s/%s' % (blog.id, post.id))
        self.assertIn('Emportez toute la série en PDF', r.text)
        self.assertIn('Obtenir les 3 articles en PDF', r.text)

    def test_standalone_wording_unchanged(self):
        blog = self.env['blog.blog'].create({'name': 'Développement Odoo'})
        post = self.env['blog.post'].create({
            'name': 'Article seul', 'blog_id': blog.id,
            'content': '<p>x</p>', 'is_published': True,
            'oski_pdf_attachment_id': self._attachment('a.pdf').id})
        r = self.url_open('/blog/%s/%s' % (blog.id, post.id))
        self.assertIn('Emportez cet article en PDF', r.text)
        self.assertIn('Obtenir cet article en PDF', r.text)

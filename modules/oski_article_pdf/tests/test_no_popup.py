import base64

from odoo.tests import HttpCase, tagged


@tagged('post_install', '-at_install')
class TestNoPopup(HttpCase):
    def setUp(self):
        super().setUp()
        self.blog = self.env['blog.blog'].create({'name': 'Développement Odoo'})
        self.post = self.env['blog.post'].create({
            'name': 'Article', 'blog_id': self.blog.id,
            'content': '<p>x</p>', 'is_published': True})
        self.post.oski_pdf_attachment_id = self.env['ir.attachment'].create({
            'name': 'g.pdf', 'datas': base64.b64encode(b'%PDF'),
            'mimetype': 'application/pdf', 'public': False})

    def test_popup_markup_absent(self):
        r = self.url_open('/blog/%s/%s' % (self.blog.id, self.post.id))
        self.assertNotIn('osk-lead-popup', r.text)

    def test_pdf_gate_still_present(self):
        r = self.url_open('/blog/%s/%s' % (self.blog.id, self.post.id))
        self.assertIn('osk-pdf-gate', r.text)

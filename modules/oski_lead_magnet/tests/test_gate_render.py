import base64
from odoo.tests import HttpCase, tagged


@tagged('post_install', '-at_install')
class TestGateRender(HttpCase):
    def _post_with_pdf(self, with_pdf):
        blog = self.env['blog.blog'].create({'name': 'B'})
        post = self.env['blog.post'].create({
            'name': 'A', 'blog_id': blog.id, 'content': '<p>x</p>', 'is_published': True})
        if with_pdf:
            post.oski_pdf_attachment_id = self.env['ir.attachment'].create({
                'name': 'a.pdf', 'datas': base64.b64encode(b'%PDF'),
                'mimetype': 'application/pdf'})
        return blog, post

    def test_cta_present_with_pdf(self):
        blog, post = self._post_with_pdf(True)
        r = self.url_open('/blog/%s/%s' % (blog.id, post.id))
        self.assertIn('osk-pdf-gate', r.text)

    def test_cta_absent_without_pdf(self):
        blog, post = self._post_with_pdf(False)
        r = self.url_open('/blog/%s/%s' % (blog.id, post.id))
        self.assertNotIn('osk-pdf-gate', r.text)

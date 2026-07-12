import base64
import json

from odoo.tests import HttpCase, tagged


@tagged('post_install', '-at_install')
class TestCaptureHttp(HttpCase):
    def _post(self, params):
        return self.url_open(
            '/oski/lead/subscribe',
            data=json.dumps({'jsonrpc': '2.0', 'method': 'call', 'params': params}),
            headers={'Content-Type': 'application/json'},
        )

    def test_route_ok_new_email(self):
        r = self._post({'email': 'http-new@example.com', 'consent': True, 'source': 'popup'})
        self.assertEqual(r.status_code, 200)
        result = r.json()['result']
        self.assertTrue(result['ok'])

    def test_route_malformed_blog_post_id_no_500(self):
        r = self._post({'email': 'http-mal@example.com', 'consent': False,
                        'source': 'pdf', 'blog_post_id': [1, 2]})
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.json()['result']['ok'])
        self.assertIsNone(r.json()['result']['pdf_url'])

    def test_route_unpublished_post_no_pdf(self):
        blog = self.env['blog.blog'].create({'name': 'B'})
        post = self.env['blog.post'].create({
            'name': 'Draft', 'blog_id': blog.id, 'is_published': False})
        post.oski_pdf_attachment_id = self.env['ir.attachment'].create({
            'name': 'd.pdf', 'datas': base64.b64encode(b'%PDF'), 'mimetype': 'application/pdf'})
        r = self._post({'email': 'http-draft@example.com', 'consent': False,
                        'source': 'pdf', 'blog_post_id': post.id})
        self.assertEqual(r.status_code, 200)
        # unpublished -> no PDF url served
        self.assertIsNone(r.json()['result']['pdf_url'])

    def test_route_consent_false_string_no_offer(self):
        # the literal string "false" must NOT be treated as consent
        self._post({'email': 'http-strfalse@example.com', 'consent': 'false', 'source': 'popup'})
        self.assertEqual(self.env['oski.welcome.offer'].search_count(
            [('email', '=', 'http-strfalse@example.com')]), 0)

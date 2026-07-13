from odoo.tests import HttpCase, tagged


@tagged('post_install', '-at_install')
class TestPopupRender(HttpCase):
    def test_popup_markup_present_on_blog(self):
        blog = self.env['blog.blog'].create({'name': 'Test'})
        post = self.env['blog.post'].create({
            'name': 'Article test', 'blog_id': blog.id,
            'content': '<p>corps</p>', 'is_published': True})
        r = self.url_open('/blog/%s/%s' % (blog.id, post.id))
        self.assertEqual(r.status_code, 200)
        self.assertIn('osk-lead-popup', r.text)

    def test_popup_absent_when_logged_in(self):
        """Visiteur connecté (compte portail = souvent déjà client) : pas de popup."""
        blog = self.env['blog.blog'].create({'name': 'Test'})
        post = self.env['blog.post'].create({
            'name': 'Article test', 'blog_id': blog.id,
            'content': '<p>corps</p>', 'is_published': True})
        self.authenticate('admin', 'admin')
        r = self.url_open('/blog/%s/%s' % (blog.id, post.id))
        self.assertEqual(r.status_code, 200)
        self.assertNotIn('osk-lead-popup', r.text)

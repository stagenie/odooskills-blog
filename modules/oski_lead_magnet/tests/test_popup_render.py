from odoo.tests import HttpCase, tagged


@tagged('post_install', '-at_install')
class TestPopupRender(HttpCase):
    """Popup retiré le 19/07/2026 (6 jours de mesure : 1 seule inscription,
    un test interne, pendant que les abonnements globaux chutaient des 2/3).
    La capture email passe désormais uniquement par le gate PDF
    (oski_article_pdf). Ces tests sont volontairement inversés pour garantir
    que le popup ne soit jamais réintroduit silencieusement."""

    def test_popup_markup_absent_on_blog(self):
        blog = self.env['blog.blog'].create({'name': 'Test'})
        post = self.env['blog.post'].create({
            'name': 'Article test', 'blog_id': blog.id,
            'content': '<p>corps</p>', 'is_published': True})
        r = self.url_open('/blog/%s/%s' % (blog.id, post.id))
        self.assertEqual(r.status_code, 200)
        self.assertNotIn('osk-lead-popup', r.text)

    def test_popup_absent_when_logged_in(self):
        """Visiteur connecté : pas de popup non plus (comme pour tout visiteur,
        le popup n'est plus rendu du tout)."""
        blog = self.env['blog.blog'].create({'name': 'Test'})
        post = self.env['blog.post'].create({
            'name': 'Article test', 'blog_id': blog.id,
            'content': '<p>corps</p>', 'is_published': True})
        self.authenticate('admin', 'admin')
        r = self.url_open('/blog/%s/%s' % (blog.id, post.id))
        self.assertEqual(r.status_code, 200)
        self.assertNotIn('osk-lead-popup', r.text)

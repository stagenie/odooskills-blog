from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestGeneratePost(TransactionCase):
    def setUp(self):
        super().setUp()
        blog = self.env['blog.blog'].create({'name': 'Développement Odoo'})
        self.post = self.env['blog.post'].create({
            'name': 'Article riche', 'blog_id': blog.id, 'is_published': True,
            'content': '<h2>Titre</h2><p>Texte</p><pre>ls -lah</pre>'
                       '<table><tr><td>a</td></tr></table>'})

    def test_generates_attachment(self):
        att = self.post._oski_generate_pdf()
        self.assertTrue(att, "doit renvoyer une pièce jointe")
        self.assertEqual(att.mimetype, 'application/pdf')
        self.assertEqual(self.post.oski_pdf_attachment_id, att)

    def test_attachment_is_a_real_pdf(self):
        import base64
        att = self.post._oski_generate_pdf()
        self.assertTrue(base64.b64decode(att.datas).startswith(b'%PDF'))

    def test_attachment_is_private(self):
        att = self.post._oski_generate_pdf()
        self.assertFalse(att.public, "le PDF ne doit pas être public (gate email)")

    def test_clears_stale_flag(self):
        self.post._oski_generate_pdf()
        self.assertFalse(self.post.oski_pdf_stale)
        self.assertTrue(self.post.oski_pdf_generated_on)

    def test_regeneration_keeps_attachment_id_and_token_stable(self):
        """Un lecteur a déjà reçu par email un lien tokenisé pointant sur
        cette pièce jointe (`/web/content/<id>?access_token=<token>`).
        Corriger une coquille dans l'article régénère le guide : ce lien
        déjà livré ne doit JAMAIS retourner 404 — l'id et le jeton doivent
        rester stables, seul le contenu change."""
        import base64
        first = self.post._oski_generate_pdf()
        first_id = first.id
        first_datas = first.datas
        first_token = first.sudo().generate_access_token()[0]

        self.post.content = '<p>réécrit</p>'
        second = self.post._oski_generate_pdf()

        self.assertEqual(
            second.id, first_id,
            "l'id de la pièce jointe doit rester stable : un lien déjà "
            "envoyé par email pointe dessus")
        self.assertEqual(
            second.access_token, first_token,
            "le jeton d'accès déjà envoyé par email doit rester valide")
        self.assertNotEqual(
            second.datas, first_datas,
            "le contenu doit refléter la nouvelle version de l'article")
        self.assertTrue(base64.b64decode(second.datas).startswith(b'%PDF'))

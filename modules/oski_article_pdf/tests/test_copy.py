from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestCopy(TransactionCase):
    """FIX3 : dupliquer un article ne doit jamais partager le PDF de
    l'original. La régénération réécrit désormais EN PLACE (même id de
    pièce jointe, cf. _oski_generate_pdf) : sans copy=False sur les 3
    champs de suivi PDF, le doublon hérite de l'attachement de l'original
    ET de son hash "à jour" ; régénérer le doublon écrase alors le PDF de
    l'ORIGINAL (son res_id est réécrit au passage), silencieusement."""

    def setUp(self):
        super().setUp()
        blog = self.env['blog.blog'].create({'name': 'Développement Odoo'})
        self.post = self.env['blog.post'].create({
            'name': 'Article original', 'blog_id': blog.id,
            'content': '<p>original</p>', 'is_published': True})
        self.post._oski_generate_pdf()

    def test_duplicate_starts_without_attachment(self):
        dup = self.post.copy()
        self.assertFalse(
            dup.oski_pdf_attachment_id,
            "un doublon ne doit jamais partager la pièce jointe PDF de "
            "l'original : la régénérer écraserait le PDF de l'original")

    def test_duplicate_starts_stale(self):
        dup = self.post.copy()
        self.assertTrue(
            dup.oski_pdf_stale,
            "un doublon sans PDF propre doit être périmé, pas hériter du "
            "hash 'à jour' de l'original")
        self.assertFalse(dup.oski_pdf_generated_on)
        self.assertFalse(dup.oski_pdf_source_hash)

    def test_regenerating_duplicate_does_not_overwrite_original(self):
        original_attachment_id = self.post.oski_pdf_attachment_id.id
        original_datas = self.post.oski_pdf_attachment_id.datas
        dup = self.post.copy()
        dup.name = 'Article dupliqué'
        dup._oski_generate_pdf()
        self.assertNotEqual(
            dup.oski_pdf_attachment_id.id, original_attachment_id,
            "régénérer le doublon doit créer SA PROPRE pièce jointe")
        self.assertEqual(
            self.env['ir.attachment'].browse(original_attachment_id).datas,
            original_datas,
            "le PDF de l'original ne doit pas avoir été écrasé par la "
            "régénération du doublon")

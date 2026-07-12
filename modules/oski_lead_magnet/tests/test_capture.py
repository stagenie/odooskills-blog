from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestCapture(TransactionCase):
    def _capture(self, email, consent=True, source='popup', post=None):
        return self.env['oski.lead.capture']._oski_capture_lead(email, consent, source, post)

    def test_disposable_rejected(self):
        res = self._capture('x@yopmail.com')
        self.assertFalse(res['ok'])
        self.assertEqual(res['error'], 'disposable')

    def test_invalid_rejected(self):
        res = self._capture('not-an-email')
        self.assertFalse(res['ok'])
        self.assertEqual(res['error'], 'invalid')

    def test_new_email_creates_offer_and_partner(self):
        res = self._capture('brand-new@example.com')
        self.assertTrue(res['ok'])
        self.assertTrue(res['new'])
        self.assertEqual(self.env['oski.welcome.offer'].search_count(
            [('email', '=', 'brand-new@example.com')]), 1)
        self.assertTrue(self.env['res.partner'].search_count(
            [('email', '=', 'brand-new@example.com')]))

    def test_consent_adds_to_mailing_list(self):
        self._capture('consenting@example.com', consent=True)
        ml = self.env['mailing.list'].search([('name', '=', 'Prospects OdooSkills')], limit=1)
        self.assertTrue(ml)
        self.assertTrue(self.env['mailing.contact'].search_count(
            [('email', '=', 'consenting@example.com'), ('list_ids', 'in', ml.ids)]))

    def test_no_consent_no_mailing_but_pdf_served(self):
        post = self.env['blog.post'].create({'name': 'P'})
        import base64
        post.oski_pdf_attachment_id = self.env['ir.attachment'].create({
            'name': 'p.pdf', 'datas': base64.b64encode(b'%PDF'), 'mimetype': 'application/pdf'})
        res = self._capture('noconsent@example.com', consent=False, source='pdf:p', post=post)
        self.assertTrue(res['ok'])
        self.assertIn('/web/content/', res['pdf_url'])
        self.assertIn('access_token=', res['pdf_url'])
        ml = self.env['mailing.list'].search([('name', '=', 'Prospects OdooSkills')], limit=1)
        if ml:
            self.assertFalse(self.env['mailing.contact'].search_count(
                [('email', '=', 'noconsent@example.com'), ('list_ids', 'in', ml.ids)]))

    def test_duplicate_email_no_second_offer(self):
        self._capture('again@example.com')
        self._capture('again@example.com')
        self.assertEqual(self.env['oski.welcome.offer'].search_count(
            [('email', '=', 'again@example.com')]), 1)

    def test_no_consent_no_offer(self):
        res = self._capture('never-consented@example.com', consent=False)
        self.assertFalse(res['new'])
        self.assertEqual(self.env['oski.welcome.offer'].search_count(
            [('email', '=', 'never-consented@example.com')]), 0)

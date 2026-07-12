import re

from odoo.tests import HttpCase, tagged


@tagged('post_install', '-at_install')
class TestLanding(HttpCase):
    def test_get_does_not_activate(self):
        # A plain GET must NOT start the 72h chrono: email link-prefetchers
        # (Outlook SafeLinks, corporate antivirus proxies) GET every link in
        # an inbound email, which would burn the window before a human clicks.
        Offer = self.env['oski.welcome.offer']
        p = self.env['res.partner'].create({'name': 'L', 'email': 'land@example.com'})
        offer = Offer.create_for_email('land@example.com', p, 'popup')
        self.assertEqual(offer.state, 'dormant')
        r = self.url_open('/oski/offer/%s' % offer.token)
        self.assertEqual(r.status_code, 200)
        offer.invalidate_recordset()
        self.assertEqual(offer.state, 'dormant')
        self.assertFalse(offer.deadline)
        # the pre-activation view must expose the human-triggered POST form
        self.assertIn('/start', r.text)

    def test_post_start_activates(self):
        # Real POST with CSRF token extracted from the GET landing page,
        # mirroring what a human clicking the "Demarrer" button does.
        Offer = self.env['oski.welcome.offer']
        p = self.env['res.partner'].create({'name': 'L2', 'email': 'land2@example.com'})
        offer = Offer.create_for_email('land2@example.com', p, 'popup')
        self.assertEqual(offer.state, 'dormant')

        r = self.url_open('/oski/offer/%s' % offer.token)
        self.assertEqual(r.status_code, 200)
        m = re.search(r'name="csrf_token"\s+value="([^"]+)"', r.text)
        self.assertTrue(m, "csrf_token input not found in landing page")
        csrf_token = m.group(1)

        r2 = self.url_open(
            '/oski/offer/%s/start' % offer.token,
            data={'csrf_token': csrf_token},
        )
        self.assertEqual(r2.status_code, 200)
        offer.invalidate_recordset()
        self.assertEqual(offer.state, 'active')
        self.assertTrue(offer.deadline)

    def test_unknown_token_404(self):
        r = self.url_open('/oski/offer/does-not-exist')
        self.assertEqual(r.status_code, 404)

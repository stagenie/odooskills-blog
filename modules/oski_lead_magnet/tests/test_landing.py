from odoo.tests import HttpCase, tagged


@tagged('post_install', '-at_install')
class TestLanding(HttpCase):
    def test_visit_activates_offer(self):
        Offer = self.env['oski.welcome.offer']
        p = self.env['res.partner'].create({'name': 'L', 'email': 'land@example.com'})
        offer = Offer.create_for_email('land@example.com', p, 'popup')
        self.assertEqual(offer.state, 'dormant')
        r = self.url_open('/oski/offer/%s' % offer.token)
        self.assertEqual(r.status_code, 200)
        offer.invalidate_recordset()
        self.assertEqual(offer.state, 'active')
        self.assertTrue(offer.deadline)

    def test_unknown_token_404(self):
        r = self.url_open('/oski/offer/does-not-exist')
        self.assertEqual(r.status_code, 404)

import json
from unittest.mock import patch, MagicMock

from dns.exception import Timeout
from dns.resolver import NXDOMAIN

from odoo.tests.common import HttpCase, tagged


@tagged('post_install', '-at_install', 'adi_odooskills_email_hygiene')
class TestSubscribeControllerHygiene(HttpCase):
    """ POST /website_mass_mailing/subscribe with various email payloads.

        Recaptcha is patched via patch.object on the ir.http registry model,
        which is the pattern used by Odoo core (see auth_signup tests).
        Our controller validates BEFORE calling super() (which runs recaptcha),
        so rejection tests don't strictly need the patch — but we apply it
        globally in setUp for consistency and to enable the "accept" test.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.test_list = cls.env['mailing.list'].create({
            'name': 'Test Hygiene List',
            'is_public': True,
        })

    def setUp(self):
        super().setUp()
        from odoo.addons.adi_odooskills_email_hygiene.models import email_validator
        email_validator._MX_CACHE.clear()

        # Establish a session with the correct database (as public/anonymous user).
        # Without this call, url_open requests are routed through the nodb routing map
        # which does not include website=True routes (website_mass_mailing/subscribe).
        self.authenticate(None, None)

        # Patch recaptcha verification using registry pattern (Odoo core style)
        def _noop_recaptcha(self, action):
            return None

        self._recaptcha_patcher = patch.object(
            self.env.registry['ir.http'],
            '_verify_request_recaptcha_token',
            _noop_recaptcha,
        )
        self._recaptcha_patcher.start()
        self.addCleanup(self._recaptcha_patcher.stop)

    def _post_subscribe(self, email):
        return self.url_open(
            '/website_mass_mailing/subscribe',
            data=json.dumps({
                'jsonrpc': '2.0',
                'method': 'call',
                'params': {
                    'list_id': self.test_list.id,
                    'value': email,
                    'subscription_type': 'email',
                },
            }),
            headers={'Content-Type': 'application/json'},
        )

    def _fake_mx(self):
        m = MagicMock()
        m.exchange.to_text.return_value = 'mx.gmail.com.'
        return m

    def test_subscribe_rejects_disposable(self):
        resp = self._post_subscribe('spam@yopmail.com')
        body = resp.json()['result']
        self.assertEqual(body.get('toast_type'), 'danger')
        self.assertIn('temporaires', body.get('toast_content', ''))
        contact = self.env['mailing.contact'].search(
            [('email', '=', 'spam@yopmail.com')]
        )
        self.assertFalse(contact, "disposable email must NOT create contact")

    def test_subscribe_rejects_role_based(self):
        with patch('dns.resolver.resolve', return_value=[self._fake_mx()]):
            resp = self._post_subscribe('info@startup.io')
        body = resp.json()['result']
        self.assertEqual(body.get('toast_type'), 'danger')
        self.assertIn('personnelle', body.get('toast_content', ''))

    def test_subscribe_rejects_no_mx(self):
        with patch('dns.resolver.resolve', side_effect=NXDOMAIN()):
            resp = self._post_subscribe('lambda@bbb.fr')
        body = resp.json()['result']
        self.assertEqual(body.get('toast_type'), 'danger')
        self.assertIn("n'accepte pas", body.get('toast_content', ''))

    def test_subscribe_rejects_dns_timeout(self):
        with patch('dns.resolver.resolve', side_effect=Timeout()):
            resp = self._post_subscribe('lambda@new-domain.io')
        body = resp.json()['result']
        self.assertEqual(body.get('toast_type'), 'danger')
        self.assertTrue(body.get('toast_content'))

    def test_subscribe_rejects_syntax_ko(self):
        resp = self._post_subscribe('not_an_email')
        body = resp.json()['result']
        self.assertEqual(body.get('toast_type'), 'danger')

    def test_subscribe_accepts_valid_email(self):
        with patch('dns.resolver.resolve', return_value=[self._fake_mx()]):
            resp = self._post_subscribe('real.user@gmail.com')
        body = resp.json()['result']
        # Native controller returns toast_type='success' on accept
        self.assertNotEqual(body.get('toast_type'), 'danger',
                            f"Expected non-danger, got: {body}")
        contact = self.env['mailing.contact'].search(
            [('email', '=', 'real.user@gmail.com')]
        )
        self.assertTrue(contact, "valid email must create contact")
        self.assertEqual(contact.email_status, 'valid')

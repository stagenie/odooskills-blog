from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install', 'adi_odooskills_email_hygiene')
class TestEmailValidatorSyntax(TransactionCase):
    """ Syntactic checks (RFC 5322 light + TLD blacklist). """

    def setUp(self):
        super().setUp()
        self.validator = self.env['email.validator']

    def test_syntax_valid_standard(self):
        status, reason = self.validator._check_syntax('pierre@gmail.com')
        self.assertEqual(status, 'ok')
        self.assertIsNone(reason)

    def test_syntax_dot_atom_with_plus_tag(self):
        status, reason = self.validator._check_syntax('prenom.nom+tag@gmail.com')
        self.assertEqual(status, 'ok')

    def test_syntax_no_at_sign(self):
        status, reason = self.validator._check_syntax('aaaaa')
        self.assertEqual(status, 'syntax_ko')
        self.assertEqual(reason, 'aaaaa')

    def test_syntax_no_tld(self):
        status, reason = self.validator._check_syntax('aaa@bbb')
        self.assertEqual(status, 'syntax_ko')

    def test_syntax_invalid_tld(self):
        status, reason = self.validator._check_syntax('pierre@boite.test')
        self.assertEqual(status, 'syntax_ko')

    def test_syntax_invalid_localhost_tld(self):
        status, reason = self.validator._check_syntax('admin@server.localhost')
        self.assertEqual(status, 'syntax_ko')

    def test_syntax_empty_string(self):
        status, reason = self.validator._check_syntax('')
        self.assertEqual(status, 'syntax_ko')

    def test_syntax_double_at(self):
        status, reason = self.validator._check_syntax('a@b@c.fr')
        self.assertEqual(status, 'syntax_ko')

    def test_syntax_unicode_idn_domain(self):
        # IDN domains must be accepted (encoded to punycode by validator)
        status, reason = self.validator._check_syntax('pierre@münchen.de')
        self.assertEqual(status, 'ok')


@tagged('post_install', '-at_install', 'adi_odooskills_email_hygiene')
class TestEmailValidatorRoleBased(TransactionCase):
    """ Reject info@, admin@, contact@ etc. """

    def setUp(self):
        super().setUp()
        self.validator = self.env['email.validator']

    def test_role_based_admin(self):
        status, reason = self.validator._check_role_based('admin', 'startup.io')
        self.assertEqual(status, 'role_based')
        self.assertEqual(reason, 'admin@startup.io')

    def test_role_based_info(self):
        status, reason = self.validator._check_role_based('info', 'boite.fr')
        self.assertEqual(status, 'role_based')
        self.assertEqual(reason, 'info@boite.fr')

    def test_role_based_postmaster(self):
        status, reason = self.validator._check_role_based('postmaster', 'boite.fr')
        self.assertEqual(status, 'role_based')

    def test_role_based_no_reply_dashed(self):
        status, reason = self.validator._check_role_based('no-reply', 'boite.fr')
        self.assertEqual(status, 'role_based')

    def test_role_based_with_plus_tag(self):
        # info+newsletter is still role-based (base part before "+" is "info")
        status, reason = self.validator._check_role_based('info+newsletter', 'boite.fr')
        self.assertEqual(status, 'role_based')
        self.assertEqual(reason, 'info+newsletter@boite.fr')

    def test_role_based_personal_passes(self):
        status, reason = self.validator._check_role_based('pierre.dupont', 'gmail.com')
        self.assertEqual(status, 'ok')
        self.assertIsNone(reason)

    def test_role_based_personal_starting_with_role_word_passes(self):
        # "infomail" is NOT role-based (full local-part doesn't match, neither does base before "+")
        status, reason = self.validator._check_role_based('infomail', 'gmail.com')
        self.assertEqual(status, 'ok')


@tagged('post_install', '-at_install', 'adi_odooskills_email_hygiene')
class TestEmailValidatorDisposable(TransactionCase):
    """ Reject yopmail, mailinator, etc. """

    def setUp(self):
        super().setUp()
        self.validator = self.env['email.validator']

    def test_disposable_yopmail(self):
        status, reason = self.validator._check_disposable('yopmail.com')
        self.assertEqual(status, 'disposable')

    def test_disposable_mailinator(self):
        status, reason = self.validator._check_disposable('mailinator.com')
        self.assertEqual(status, 'disposable')

    def test_disposable_10minutemail(self):
        status, reason = self.validator._check_disposable('10minutemail.com')
        self.assertEqual(status, 'disposable')

    def test_disposable_legit_passes(self):
        status, reason = self.validator._check_disposable('gmail.com')
        self.assertEqual(status, 'ok')

    def test_disposable_uppercase_normalized(self):
        # caller is expected to lowercase before calling, but defense in depth
        status, reason = self.validator._check_disposable('YOPMAIL.COM')
        self.assertEqual(status, 'disposable')

    def test_disposable_corp_domain_passes(self):
        status, reason = self.validator._check_disposable('adicops.com')
        self.assertEqual(status, 'ok')


from unittest.mock import patch, MagicMock
import dns.resolver
from dns.exception import Timeout
from dns.resolver import NXDOMAIN, NoAnswer


@tagged('post_install', '-at_install', 'adi_odooskills_email_hygiene')
class TestEmailValidatorMx(TransactionCase):
    """ DNS MX resolution with TTL cache. """

    def setUp(self):
        super().setUp()
        self.validator = self.env['email.validator']
        # Reset cache between tests to avoid leakage
        from odoo.addons.adi_odooskills_email_hygiene.models import email_validator
        email_validator._MX_CACHE.clear()

    def _fake_mx(self, host):
        m = MagicMock()
        m.exchange.to_text.return_value = host
        return m

    def test_mx_present(self):
        with patch('dns.resolver.resolve', return_value=[self._fake_mx('mx.gmail.com.')]):
            status, reason = self.validator._resolve_mx('gmail.com')
        self.assertEqual(status, 'ok')

    def test_mx_nxdomain(self):
        with patch('dns.resolver.resolve', side_effect=NXDOMAIN()):
            status, reason = self.validator._resolve_mx('aaa.bbb.fr')
        self.assertEqual(status, 'mx_ko')

    def test_mx_no_answer(self):
        with patch('dns.resolver.resolve', side_effect=NoAnswer()):
            status, reason = self.validator._resolve_mx('domain-without-mx.fr')
        self.assertEqual(status, 'mx_ko')

    def test_mx_timeout(self):
        with patch('dns.resolver.resolve', side_effect=Timeout()):
            status, reason = self.validator._resolve_mx('slow-dns.com')
        self.assertEqual(status, 'dns_timeout')

    def test_mx_cache_hit_avoids_second_resolve(self):
        with patch('dns.resolver.resolve', return_value=[self._fake_mx('mx.x.com.')]) as mock:
            self.validator._resolve_mx('cached.com')
            self.validator._resolve_mx('cached.com')
        self.assertEqual(mock.call_count, 1, "Second call should hit cache")

    def test_mx_cache_negative_result_cached(self):
        # NXDOMAIN must also be cached (avoid hammering DNS on garbage)
        with patch('dns.resolver.resolve', side_effect=NXDOMAIN()) as mock:
            self.validator._resolve_mx('nope.fr')
            self.validator._resolve_mx('nope.fr')
        self.assertEqual(mock.call_count, 1)

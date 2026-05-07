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
        self.assertIsNone(reason)

    def test_mx_nxdomain(self):
        with patch('dns.resolver.resolve', side_effect=NXDOMAIN()):
            status, reason = self.validator._resolve_mx('aaa.bbb.fr')
        self.assertEqual(status, 'mx_ko')
        self.assertEqual(reason, 'aaa.bbb.fr')

    def test_mx_no_answer(self):
        with patch('dns.resolver.resolve', side_effect=NoAnswer()):
            status, reason = self.validator._resolve_mx('domain-without-mx.fr')
        self.assertEqual(status, 'mx_ko')

    def test_mx_timeout(self):
        with patch('dns.resolver.resolve', side_effect=Timeout()):
            status, reason = self.validator._resolve_mx('slow-dns.com')
        self.assertEqual(status, 'dns_timeout')
        self.assertEqual(reason, 'slow-dns.com')

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

    def test_mx_timeout_uses_short_ttl(self):
        """ dns_timeout entries must NOT be cached at full TTL_SEC,
            otherwise a transient DNS flake blocks a user for 1h. """
        from odoo.addons.adi_odooskills_email_hygiene.models import email_validator
        with patch('dns.resolver.resolve', side_effect=Timeout()):
            self.validator._resolve_mx('flaky.example.com')
        # Cache entry exists with the short TTL
        cached = email_validator._MX_CACHE.get('flaky.example.com')
        self.assertIsNotNone(cached, "timeout result should be cached")
        status, expiry = cached
        self.assertEqual(status, 'dns_timeout')
        # Expiry should be within MX_CACHE_TTL_TIMEOUT_SEC (60s) from now,
        # well under MX_CACHE_TTL_SEC (3600s)
        import time as _time
        seconds_until_expiry = expiry - _time.monotonic()
        self.assertLess(seconds_until_expiry, email_validator.MX_CACHE_TTL_SEC,
                        "dns_timeout entry should NOT use the full 1h TTL")
        self.assertLessEqual(seconds_until_expiry, email_validator.MX_CACHE_TTL_TIMEOUT_SEC + 1,
                             "dns_timeout entry should use the short TTL")


@tagged('post_install', '-at_install', 'adi_odooskills_email_hygiene')
class TestEmailValidatorOrchestration(TransactionCase):
    """ End-to-end validate() routing: syntax → role-based → disposable → MX. """

    def setUp(self):
        super().setUp()
        self.validator = self.env['email.validator']
        from odoo.addons.adi_odooskills_email_hygiene.models import email_validator
        email_validator._MX_CACHE.clear()

    def _fake_mx(self):
        m = MagicMock()
        m.exchange.to_text.return_value = 'mx.gmail.com.'
        return m

    def test_validate_valid(self):
        with patch('dns.resolver.resolve', return_value=[self._fake_mx()]):
            status, reason = self.validator.validate('pierre@gmail.com')
        self.assertEqual(status, 'valid')
        self.assertIsNone(reason)

    def test_validate_syntax_ko_short_circuits(self):
        # MX should NOT be queried when syntax fails
        with patch('dns.resolver.resolve') as mock:
            status, reason = self.validator.validate('aaa@bbb')
        self.assertEqual(status, 'syntax_ko')
        self.assertEqual(reason, 'aaa@bbb')
        mock.assert_not_called()

    def test_validate_role_based_short_circuits(self):
        with patch('dns.resolver.resolve') as mock:
            status, reason = self.validator.validate('info@startup.io')
        self.assertEqual(status, 'role_based')
        self.assertEqual(reason, 'info@startup.io')
        mock.assert_not_called()

    def test_validate_disposable_short_circuits(self):
        with patch('dns.resolver.resolve') as mock:
            status, reason = self.validator.validate('test@yopmail.com')
        self.assertEqual(status, 'disposable')
        self.assertEqual(reason, 'test@yopmail.com')
        mock.assert_not_called()

    def test_validate_mx_ko(self):
        with patch('dns.resolver.resolve', side_effect=NXDOMAIN()):
            status, reason = self.validator.validate('aaa@bbb.fr')
        self.assertEqual(status, 'mx_ko')
        self.assertEqual(reason, 'aaa@bbb.fr')

    def test_validate_dns_timeout(self):
        with patch('dns.resolver.resolve', side_effect=Timeout()):
            status, reason = self.validator.validate('pierre@new-domain.io')
        self.assertEqual(status, 'dns_timeout')
        self.assertEqual(reason, 'pierre@new-domain.io')

    def test_validate_normalizes_case(self):
        with patch('dns.resolver.resolve', return_value=[self._fake_mx()]):
            status, reason = self.validator.validate('PiErRe@GMail.cOm')
        self.assertEqual(status, 'valid')

    def test_validate_empty_input(self):
        status, reason = self.validator.validate('')
        self.assertEqual(status, 'syntax_ko')

    def test_validate_none_input(self):
        status, reason = self.validator.validate(None)
        self.assertEqual(status, 'syntax_ko')


@tagged('post_install', '-at_install', 'adi_odooskills_email_hygiene')
class TestEmailValidatorBatch(TransactionCase):
    """ Batch validation with progress logging (used by sub-project B cleanup). """

    def setUp(self):
        super().setUp()
        self.validator = self.env['email.validator']
        from odoo.addons.adi_odooskills_email_hygiene.models import email_validator
        email_validator._MX_CACHE.clear()

    def _fake_mx(self):
        m = MagicMock()
        m.exchange.to_text.return_value = 'mx.gmail.com.'
        return m

    def test_batch_returns_per_email_status(self):
        emails = ['pierre@gmail.com', 'aaa@bbb', 'spam@yopmail.com']
        with patch('dns.resolver.resolve', return_value=[self._fake_mx()]):
            results = self.validator.validate_batch(emails)
        self.assertEqual(len(results), 3)
        statuses = {r['email']: r['status'] for r in results}
        self.assertEqual(statuses['pierre@gmail.com'], 'valid')
        self.assertEqual(statuses['aaa@bbb'], 'syntax_ko')
        self.assertEqual(statuses['spam@yopmail.com'], 'disposable')

    def test_batch_logs_progress_every_n(self):
        # 25 emails, progress_every=10 → expect 3 progress logs (10, 20, 25)
        emails = [f"user{i}@yopmail.com" for i in range(25)]
        with patch('odoo.addons.adi_odooskills_email_hygiene.models.email_validator._logger') as mock_log:
            self.validator.validate_batch(emails, progress_every=10)
        info_calls = [c for c in mock_log.info.call_args_list
                      if 'validate_batch progress' in (c.args[0] if c.args else '')]
        self.assertEqual(len(info_calls), 3,
                         f"Expected 3 progress calls (10/25, 20/25, 25/25), got: {info_calls}")

    def test_batch_empty_input(self):
        results = self.validator.validate_batch([])
        self.assertEqual(results, [])

    def test_batch_default_progress_every_100(self):
        # 50 emails with default progress_every=100 → expect 1 final log (50/50)
        emails = [f"user{i}@yopmail.com" for i in range(50)]
        with patch('odoo.addons.adi_odooskills_email_hygiene.models.email_validator._logger') as mock_log:
            self.validator.validate_batch(emails)
        info_calls = [c for c in mock_log.info.call_args_list
                      if 'validate_batch progress' in (c.args[0] if c.args else '')]
        self.assertEqual(len(info_calls), 1)


@tagged('post_install', '-at_install', 'adi_odooskills_email_hygiene')
class TestMailingContactEmailStatus(TransactionCase):
    """ Verify the email_status field is present and defaults to 'valid'. """

    def test_email_status_field_exists(self):
        Contact = self.env['mailing.contact']
        self.assertIn('email_status', Contact._fields)

    def test_email_status_default_valid(self):
        contact = self.env['mailing.contact'].create({
            'name': 'Test User',
            'email': 'test@example.com',
        })
        self.assertEqual(contact.email_status, 'valid')

    def test_email_status_selection_includes_all_reasons(self):
        Contact = self.env['mailing.contact']
        selection = dict(Contact._fields['email_status'].selection)
        for code in ('valid', 'syntax_ko', 'role_based', 'disposable',
                     'mx_ko', 'dns_timeout'):
            self.assertIn(code, selection,
                          f"email_status missing selection key '{code}'")

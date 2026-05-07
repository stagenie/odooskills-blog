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

    def test_syntax_dot_atom_with_plus_tag(self):
        status, reason = self.validator._check_syntax('prenom.nom+tag@gmail.com')
        self.assertEqual(status, 'ok')

    def test_syntax_no_at_sign(self):
        status, reason = self.validator._check_syntax('aaaaa')
        self.assertEqual(status, 'syntax_ko')

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

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

    def test_role_based_info(self):
        status, reason = self.validator._check_role_based('info', 'boite.fr')
        self.assertEqual(status, 'role_based')

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

    def test_role_based_personal_passes(self):
        status, reason = self.validator._check_role_based('pierre.dupont', 'gmail.com')
        self.assertEqual(status, 'ok')

    def test_role_based_personal_starting_with_role_word_passes(self):
        # "infomail" is NOT role-based (full local-part doesn't match, neither does base before "+")
        status, reason = self.validator._check_role_based('infomail', 'gmail.com')
        self.assertEqual(status, 'ok')

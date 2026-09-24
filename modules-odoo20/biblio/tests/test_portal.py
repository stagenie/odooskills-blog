from odoo.tests import HttpCase, new_test_user


class TestPortal(HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        book = cls.env['library.book'].create({'title': "OWL 3 : le front-end d'Odoo"})
        copy_1, copy_2, copy_3 = cls.env['library.copy'].create([{'book_id': book.id} for _ in range(3)])
        cls.member = cls.env['library.member'].create({'name': "Adhérent portail", 'card_number': 'P-0001'})
        other = cls.env['library.member'].create({'name': "Autre adhérent", 'card_number': 'P-0002'})
        cls.portal_user = new_test_user(
            cls.env, login='adherent_portail', groups='base.group_portal',
            partner_id=cls.member.partner_id.id,
        )
        cls.own_loan = cls.env['library.loan'].create({'member_id': cls.member.id, 'copy_id': copy_1.id})
        cls.env['library.loan'].create({'member_id': cls.member.id, 'copy_id': copy_2.id})
        cls.other_loan = cls.env['library.loan'].create({'member_id': other.id, 'copy_id': copy_3.id})

    def test_portal_lists_only_own_loans(self):
        self.authenticate('adherent_portail', 'adherent_portail')
        response = self.url_open('/my/loans')
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.own_loan.reference, response.text)
        self.assertNotIn(self.other_loan.reference, response.text)

    def test_home_counter_is_exact(self):
        self.authenticate('adherent_portail', 'adherent_portail')
        result = self.make_jsonrpc_request('/my/counters', {'counters': {'library_loan_count': 'common_category'}})
        self.assertEqual(result['library_loan_count'], 2)

    def test_portal_cannot_open_other_loan(self):
        self.authenticate('adherent_portail', 'adherent_portail')
        response = self.url_open(f'/my/loans/{self.other_loan.id}', allow_redirects=False)
        self.assertEqual(response.status_code, 303)
        self.assertTrue(response.headers['Location'].endswith('/my'))

    def test_share_link_opens_loan_without_account(self):
        self.authenticate(None, None)
        response = self.url_open(self.other_loan._get_share_url())
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.other_loan.reference, response.text)

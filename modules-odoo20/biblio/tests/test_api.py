from datetime import datetime, timedelta

from odoo.tests import HttpCase, new_test_user


class TestApi(HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env['res.lang']._activate_lang('fr_FR')
        book = cls.env['library.book'].create({'title': "Python pour Odoo"})
        cls.copy_1, cls.copy_2 = cls.env['library.copy'].create([{'book_id': book.id}, {'book_id': book.id}])
        member = cls.env['library.member'].create({'name': "Service Formation", 'card_number': 'A-0001'})
        cls.late = cls.env['library.loan'].create({
            'member_id': member.id, 'copy_id': cls.copy_1.id,
            'date_out': datetime.now().date() - timedelta(days=30),
        })
        cls.on_time = cls.env['library.loan'].create({'member_id': member.id, 'copy_id': cls.copy_2.id})
        api_user = new_test_user(cls.env, login='test_api', groups='biblio.group_library_desk')
        cls.key = cls.env['res.users.apikeys'].with_user(api_user)._generate(
            'rpc', "Tests", datetime.now() + timedelta(days=1))

    def _call(self, method, **params):
        return self.url_open(
            f'/json/2/library.loan/{method}',
            json=params,
            headers={
                'Authorization': f'bearer {self.key}',
                'X-Odoo-Database': self.env.cr.dbname,
            },
        )

    def test_late_loans(self):
        response = self._call('api_loans', late=True)
        self.assertEqual(response.status_code, 200)
        loans = {loan['reference']: loan for loan in response.json()}
        self.assertNotIn(self.on_time.reference, loans)
        self.assertGreater(loans[self.late.reference]['days_late'], 0)
        self.assertIsNone(loans[self.late.reference]['date_return'])

    def test_return_copy(self):
        response = self._call('api_return_copy', copy=self.copy_1.name)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.late.state, 'returned')
        again = self._call('api_return_copy', copy=self.copy_1.name, context={'lang': 'fr_FR'})
        self.assertEqual(again.status_code, 422)
        self.assertIn(self.copy_1.name, again.json()['message'])
        self.assertNotIn('Traceback', again.json()['debug'])

    def test_private_and_forbidden(self):
        self.assertEqual(self._call('_api_values', ids=self.late.ids).status_code, 403)
        self.assertEqual(self._call('unlink', ids=self.late.ids).status_code, 403)

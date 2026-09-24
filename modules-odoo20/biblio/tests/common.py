from odoo.tests import TransactionCase, new_test_user


class BiblioCase(TransactionCase):
    """Jeu de données commun : un livre, deux exemplaires, un adhérent, deux utilisateurs."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_desk = new_test_user(cls.env, login='test_accueil', groups='biblio.group_library_desk')
        cls.user_manager = new_test_user(cls.env, login='test_biblio', groups='biblio.group_library_manager')
        cls.book = cls.env['library.book'].create({'title': "Python pour Odoo"})
        cls.copy_1, cls.copy_2 = cls.env['library.copy'].create([
            {'book_id': cls.book.id},
            {'book_id': cls.book.id},
        ])
        cls.member = cls.env['library.member'].create({
            'name': "Équipe Formation",
            'email': 'formation@example.com',
            'card_number': 'T-0001',
        })

    @classmethod
    def _emprunter(cls, copy, **vals):
        return cls.env['library.loan'].create({
            'member_id': cls.member.id,
            'copy_id': copy.id,
            **vals,
        })

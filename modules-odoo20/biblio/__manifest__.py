{
    'name': "Bibliothèque",
    'summary': "Gérer les livres d'une bibliothèque",
    'description': """
Premier module de la série « Développer avec Odoo 20 ».
Un modèle Livre, ses droits d'accès, sa liste, son formulaire et son menu.
    """,
    'author': "OdooSkills",
    'website': "https://odooskills.com",
    'category': 'Services',
    'version': '20.0.1.5.0',
    'license': 'LGPL-3',
    'depends': ['base'],
    'data': [
        'security/ir.access.csv',
        'data/library_sequence.xml',
        'data/library_cron.xml',
        'views/library_book_views.xml',
        'views/library_copy_views.xml',
        'views/library_member_views.xml',
        'views/library_loan_views.xml',
    ],
    'application': True,
}

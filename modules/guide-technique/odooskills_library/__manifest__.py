{
    'name': 'Bibliothèque',
    'version': '19.0.1.0.0',
    'category': 'Services',
    'summary': 'Gestion simple de livres',
    'author': 'OdooSkills',
    'website': 'https://odooskills.com',
    'license': 'LGPL-3',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'views/book_views.xml',
    ],
    'installable': True,
    'application': True,
}

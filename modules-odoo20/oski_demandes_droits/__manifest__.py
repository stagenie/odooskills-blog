{
    'name': "Demandes internes : sécuriser un module (exemple)",
    'version': '20.0.1.0.0',
    'summary': "Exemple de sécurité Odoo 20 : ir.access avec domaine, groupes, sudo, contrôleurs",
    'category': 'Productivity',
    'author': 'OdooSkills',
    'website': 'https://odooskills.com',
    'license': 'LGPL-3',
    'depends': ['base', 'web'],
    'data': [
        # les groupes d'abord : ir.access.csv y fait référence
        'security/oski_demandes_security.xml',
        'security/ir.access.csv',
        'views/oski_demande_views.xml',
    ],
    'application': True,
    'installable': True,
}

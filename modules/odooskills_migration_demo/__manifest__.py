{
    'name': 'OdooSkills — Migration demo',
    'version': '19.0.1.1.0',
    'category': 'Tools',
    'summary': "Module démo pour l'article T25 — scripts de migration Odoo 19",
    'author': 'OdooSkills',
    'license': 'LGPL-3',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'views/mig_demo_item_views.xml',
    ],
    'installable': True,
    'application': False,
}

{
    'name': 'Catalogue des widgets de champ (exemple)',
    'version': '20.0.1.0.0',
    'category': 'Hidden',
    'summary': "Une fiche, une liste et une carte qui montrent les widgets de champ standard d'Odoo 20",
    'author': 'OdooSkills',
    'license': 'LGPL-3',
    'depends': ['web'],
    'data': [
        'security/ir.access.csv',
        'views/widget_demo_views.xml',
    ],
    'demo': [
        'data/widget_demo_demo.xml',
    ],
    'installable': True,
}

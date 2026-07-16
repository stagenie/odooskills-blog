{
    'name': 'Démo Traduction — Champ traduisible',
    'version': '19.0.1.0.0',
    'category': 'Tools',
    'summary': "Module d'exemple : champ translate=True et stockage jsonb (article OdooSkills)",
    'author': 'OdooSkills',
    'license': 'LGPL-3',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'views/trad_demo_views.xml',
        'report/trad_demo_report.xml',
    ],
    'installable': True,
    'application': False,
}

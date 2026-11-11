{
    'name': 'Parc de matériel prêté',
    'version': '20.0.1.1.0',
    'summary': 'Suivre le matériel prêté aux contacts',
    'category': 'Tools',
    'author': 'OdooSkills',
    'license': 'LGPL-3',
    'depends': ['web'],
    'data': [
        'views/materiel_views.xml',
        'report/materiel_report.xml',
        'security/ir.access.csv',
    ],
}

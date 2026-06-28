{
    'name': 'OdooSkills — Fiche contact PDF (rapport from scratch)',
    'version': '19.0.1.0.0',
    'category': 'Technical',
    'summary': 'Créer un rapport PDF QWeb de A à Z : paperformat, action et template sur res.partner',
    'description': """
Module fil rouge de l'article « Créer son rapport PDF de A à Z ».
Construit un rapport entièrement nouveau — une fiche contact — sans hériter
d'aucun rapport existant : un format papier dédié, une action ir.actions.report
et un template QWeb appuyé sur la mise en page société standard.
""",
    'author': 'OdooSkills',
    'website': 'https://odooskills.com',
    'license': 'LGPL-3',
    'depends': ['contacts'],
    'data': [
        'report/contact_report.xml',
    ],
    'installable': True,
    'application': False,
}

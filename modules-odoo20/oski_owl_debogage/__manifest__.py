{
    'name': "Devis par commercial (démo débogage OWL 3)",
    'summary': "Action client OWL 3 qui totalise les devis en cours par commercial : support d'exercice de débogage",
    'description': """
Action client OWL 3 : devis en cours (brouillon ou envoyés) regroupés par commercial, avec leur total HT.
Module d'exemple du blog OdooSkills, utilisé pour montrer le mode debug, la console et les points d'arrêt.
    """,
    'version': '20.0.1.0.0',
    'category': 'Hidden',
    'author': "OdooSkills",
    'website': "https://odooskills.com",
    'license': 'LGPL-3',
    'depends': ['sale'],
    'data': [
        'views/devis_action.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'oski_owl_debogage/static/src/**/*',
        ],
        'web.assets_unit_tests': [
            'oski_owl_debogage/static/tests/**/*',
        ],
    },
}

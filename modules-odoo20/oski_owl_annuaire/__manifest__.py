{
    'name': "Annuaire express (démo OWL 3)",
    'summary': "Un composant OWL 3 de A à Z : props, état, hooks, gabarit et test Hoot",
    'description': """
Action client OWL 3 qui liste les sociétés, filtre à la frappe et garde des favoris
dans le navigateur. Module d'exemple du blog OdooSkills.
    """,
    'version': '20.0.1.0.0',
    'category': 'Hidden',
    'author': "OdooSkills",
    'website': "https://odooskills.com",
    'license': 'LGPL-3',
    'depends': ['web'],
    'data': [
        'views/annuaire_action.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'oski_owl_annuaire/static/src/**/*',
        ],
        'web.assets_unit_tests': [
            'oski_owl_annuaire/static/tests/**/*',
        ],
    },
    'application': True,
}

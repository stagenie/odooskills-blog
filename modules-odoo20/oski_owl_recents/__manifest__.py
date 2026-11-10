{
    'name': "Derniers consultés (démo patch, registres, services OWL 3)",
    'summary': "Étendre le client web d'Odoo 20 sans le casser : un service, un patch du formulaire, "
               "une entrée du systray et du menu utilisateur",
    'description': """
Garde la liste des derniers enregistrements ouverts en formulaire et les propose
dans la barre du haut. Module d'exemple du blog OdooSkills.
    """,
    'version': '20.0.1.0.0',
    'category': 'Hidden',
    'author': "OdooSkills",
    'website': "https://odooskills.com",
    'license': 'LGPL-3',
    'depends': ['web'],
    'assets': {
        'web.assets_backend': [
            'oski_owl_recents/static/src/**/*',
        ],
        'web.assets_unit_tests': [
            'oski_owl_recents/static/tests/**/*',
        ],
    },
}

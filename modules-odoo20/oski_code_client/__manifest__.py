{
    'name': 'Code client (exemple de tests)',
    'version': '20.0.1.0.0',
    'category': 'Sales/CRM',
    'summary': 'Un code client sur les contacts, une route JSON et les tests qui les couvrent : TransactionCase, HttpCase, tour',
    'author': 'OdooSkills',
    'license': 'LGPL-3',
    'depends': ['contacts'],
    'data': ['views/res_partner_views.xml'],
    'assets': {
        'web.assets_tests': ['oski_code_client/static/tests/tours/**/*'],
    },
    'installable': True,
}

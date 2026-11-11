{
    'name': 'Rapport PDF de commande (exemple)',
    'version': '20.0.1.0.0',
    'category': 'Sales',
    'summary': 'Sauts de page, formats de date, police et en-têtes dans un rapport QWeb PDF',
    'author': 'OdooSkills',
    'license': 'LGPL-3',
    'depends': ['sale'],
    'data': [
        'report/report_paperformat.xml',
        'report/report_commande.xml',
    ],
    'assets': {
        'web.report_assets_common': [
            'oski_qweb_pdf/static/src/scss/report_commande.scss',
        ],
    },
    'installable': True,
}

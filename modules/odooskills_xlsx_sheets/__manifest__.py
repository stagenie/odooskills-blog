{
    'name': 'OdooSkills — Rapport XLSX multi-feuilles (démo blog)',
    'version': '19.0.1.0.0',
    'category': 'Tools',
    'summary': "Démo d'article : classeur Excel à plusieurs feuilles — une feuille "
               "par commercial, feuille sommaire avec liens internes (write_url) et "
               "totaux par feuille",
    'author': 'OdooSkills',
    'website': 'https://odooskills.com',
    'license': 'LGPL-3',
    'depends': ['sale'],
    'data': [
        'views/sale_order_views.xml',
    ],
    'installable': True,
    'application': False,
}

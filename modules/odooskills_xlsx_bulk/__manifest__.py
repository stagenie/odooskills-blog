{
    'name': 'OdooSkills — Rapport XLSX gros volumes (démo blog)',
    'version': '19.0.1.0.0',
    'category': 'Tools',
    'summary': "Démo d'article : rapport Excel sur gros volumes — agrégation SQL "
               "(_read_group) sans charger les enregistrements et écriture en flux "
               "à mémoire constante (constant_memory)",
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

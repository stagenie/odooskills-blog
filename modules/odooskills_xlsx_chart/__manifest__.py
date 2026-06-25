{
    'name': 'OdooSkills — Graphiques dans un rapport XLSX (démo blog)',
    'version': '19.0.1.0.0',
    'category': 'Tools',
    'summary': "Démo d'article : insérer des graphiques natifs Excel (.xlsx) — "
               "histogramme, camembert et courbe — dans un rapport de ventes avec "
               "xlsxwriter (add_chart / insert_chart)",
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

{
    'name': 'OdooSkills - Parcours de lecture du blog',
    'version': '19.0.1.1.0',
    'category': 'Website/Website',
    'summary': "Séries d'articles dans l'ordre de lecture, page /parcours et versions d'Odoo",
    'description': """
Parcours de lecture du blog OdooSkills
======================================
- Séries d'articles ordonnées, rattachées automatiquement par étiquette.
- Page /parcours par version d'Odoo, séries « toutes versions » dans chaque onglet.
- Bandeau en tête des listes de blog et repère « étape n/N » dans chaque article de série.
""",
    'author': 'ADICOPS',
    'website': 'https://odooskills.com',
    'license': 'LGPL-3',
    'depends': ['website_blog'],
    'data': [
        'security/ir.model.access.csv',
        'data/odoo_version_data.xml',
        'views/oski_blog_series_views.xml',
        'views/parcours_templates.xml',
        'views/blog_templates.xml',
    ],
    'post_init_hook': 'post_init',
    'uninstall_hook': 'uninstall_hook',
    'installable': True,
    'application': False,
}

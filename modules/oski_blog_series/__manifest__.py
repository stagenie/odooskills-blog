{
    'name': 'OdooSkills - Parcours de lecture du blog',
    'version': '19.0.1.0.0',
    'category': 'Website/Website',
    'summary': "Séries d'articles dans l'ordre de lecture, page /parcours et versions d'Odoo",
    'author': 'ADICOPS',
    'website': 'https://odooskills.com',
    'license': 'LGPL-3',
    'depends': ['website_blog'],
    'data': [
        'security/ir.model.access.csv',
        'data/odoo_version_data.xml',
        'views/parcours_templates.xml',
        'views/blog_templates.xml',
    ],
    'post_init_hook': 'post_init',
    'installable': True,
    'application': False,
}

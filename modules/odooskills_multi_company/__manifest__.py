{
    'name': "OdooSkills — Démo multi-société",
    'version': '19.0.1.0.0',
    'summary': "Module compagnon de l'article « Développer un module multi-société en Odoo 19 »",
    'category': 'Tutorials',
    'author': 'OdooSkills',
    'website': 'https://odooskills.com',
    'license': 'LGPL-3',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'security/ir_rules.xml',
        'data/ir_cron.xml',
        'views/work_order_views.xml',
    ],
    'post_init_hook': '_create_company_sequences',
    'installable': True,
}

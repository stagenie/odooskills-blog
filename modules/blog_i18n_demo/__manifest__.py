{
    'name': 'Démo i18n — Traduire son module',
    'version': '19.0.1.0.0',
    'category': 'Tools',
    'summary': "Module d'exemple : _(), QWeb et _t traduits via .pot/.po (article OdooSkills)",
    'author': 'OdooSkills',
    'license': 'LGPL-3',
    'depends': ['base', 'web'],
    'data': [
        'security/ir.model.access.csv',
        'views/order_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'blog_i18n_demo/static/src/js/greeting.js',
        ],
    },
    'installable': True,
    'application': False,
}

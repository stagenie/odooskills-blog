{
    'name': 'OdooSkills - Promotions dynamiques',
    'version': '19.0.3.1.0',
    'category': 'Website/Website',
    'summary': "Campagnes promo datées : prix, bandeau et compte à rebours dynamiques",
    'author': 'ADICOPS',
    'website': 'https://odooskills.com',
    'license': 'LGPL-3',
    'depends': ['oski_ebook_lifecycle', 'website_sale', 'sale_loyalty'],
    'data': [
        'security/ir.model.access.csv',
        'views/templates.xml',
        'views/oski_promo_campaign_views.xml',
        'views/product_template_views.xml',
        'views/loyalty_views.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'oski_promo/static/src/scss/oski_promo.scss',
            'oski_promo/static/src/js/oski_promo_countdown.js',
        ],
    },
    'installable': True,
    'application': False,
}

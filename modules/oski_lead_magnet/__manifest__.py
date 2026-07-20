{
    'name': 'OdooSkills - Capture Email & Offre Bienvenue',
    'version': '19.0.1.4.0',
    'category': 'Website/Marketing',
    'summary': "Popup + gate PDF de capture email et coupon personnel de bienvenue (taux et durée configurables)",
    'author': 'ADICOPS',
    'website': 'https://odooskills.com',
    'license': 'LGPL-3',
    'depends': [
        'website_blog', 'website_sale', 'loyalty', 'sale_loyalty', 'mass_mailing',
        'oski_ebook_lifecycle',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/config_params.xml',
        'data/loyalty_program.xml',
        'data/mail_template_welcome.xml',
        'data/ir_cron.xml',
        'views/blog_post_views.xml',
        'views/res_config_settings_views.xml',
        'views/offer_landing.xml',
        'views/popup_templates.xml',
        'views/pdf_gate_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'oski_lead_magnet/static/src/js/offer_countdown.js',
            'oski_lead_magnet/static/src/js/lead_popup.js',
            'oski_lead_magnet/static/src/scss/lead_magnet.scss',
        ],
    },
    'installable': True,
    'application': False,
}

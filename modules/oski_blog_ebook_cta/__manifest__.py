{
    'name': 'OdooSkills - Bandes CTA Ebook sur Blog',
    'version': '19.0.2.0.0',
    'category': 'Website/Marketing',
    'summary': "Bande CTA contextuelle vers les ebooks en fin d'article de blog (édition 20 par défaut, 19 pour les articles Odoo 19)",
    'author': 'ADICOPS',
    'website': 'https://odooskills.com',
    'license': 'LGPL-3',
    'depends': ['website_blog', 'website_sale', 'oski_promo'],
    'data': [
        'views/blog_cta_templates.xml',
    ],
    'installable': True,
    'application': False,
}

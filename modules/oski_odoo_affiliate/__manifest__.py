{
    'name': 'OdooSkills - Lien Affiliation Odoo',
    'version': '19.0.1.0.0',
    'category': 'Website/Marketing',
    'summary': "Insère le lien d'affiliation Odoo (footer, fin d'article, pastille) sur le blog",
    'description': """
OdooSkills - Lien Affiliation Odoo
==================================

Monétise le blog via le programme de parrainage Odoo :

- Remplace le lien "Powered by Odoo" du footer par le lien d'affiliation.
- Ajoute une bande CTA "Essayer Odoo gratuitement" en fin d'article.
- Ajoute une petite pastille flottante persistante sur les pages d'articles.

Tous les liens s'ouvrent dans un nouvel onglet (target=_blank) avec
rel="sponsored noopener nofollow" (bonnes pratiques SEO pour liens affiliés).

L'URL d'affiliation est stockée dans le paramètre système
``oski.odoo_affiliate_url`` (modifiable sans toucher au code).
    """,
    'author': 'ADICOPS',
    'website': 'https://odooskills.com',
    'license': 'LGPL-3',
    'depends': ['website', 'website_blog'],
    'data': [
        'data/affiliate_data.xml',
        'views/affiliate_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'oski_odoo_affiliate/static/src/scss/affiliate.scss',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}

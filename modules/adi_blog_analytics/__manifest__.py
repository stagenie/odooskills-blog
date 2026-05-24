{
    'name': 'ADI - Blog Analytics',
    'version': '19.0.2.0.0',
    'category': 'Marketing',
    'summary': "Tableau de bord backend : inscrits newsletter, vues d'articles, top articles, visiteurs & pays, filtres temps",
    'description': """
Module 100% XML (zéro Python métier). Ajoute une application "Blog Analytics" avec :
- Inscrits newsletter (par jour, par pays) — avec total inscrits en pivot
- Vues d'articles blog (par jour) — avec total vues en pivot
- Top articles (ordre visits DESC)
- Visiteurs & Pays (visiteurs uniques géolocalisés, total visites + total pages vues en footer liste)
- Filtres temps unifiés : Aujourd'hui / Ce mois / Mois dernier / 7j / 30j

S'appuie exclusivement sur les modèles natifs Odoo (mailing.contact, website.track, website.visitor, blog.post).
Compagnon recommandé : adi_blog_geoip (résolution pays automatique sur inscription).
""",
    'author': 'ADICOPS',
    'website': 'https://odooskills.com',
    'license': 'LGPL-3',
    'depends': [
        'website_blog',
        'mass_mailing',
        'website',
    ],
    'data': [
        'security/res_groups.xml',
        'security/ir.model.access.csv',
        'views/mailing_contact_views.xml',
        'views/website_track_views.xml',
        'views/website_visitor_views.xml',
        'views/blog_post_analytics_views.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'images': ['static/description/icon.png'],
}

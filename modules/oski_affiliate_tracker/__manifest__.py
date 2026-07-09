{
    'name': "Affiliations",
    'version': '19.0.1.1.1',
    'category': 'Marketing',
    'summary': "Suivi personnel des programmes d'affiliation et des commissions",
    'description': """
Gérez au même endroit tous vos programmes d'affiliation (Amazon, SaaS, hébergeurs…) :
identifiants de connexion (par pointeur sécurisé), liens, taux de commission, et
saisie manuelle de chaque commission encaissée. Statistiques par programme, par
période et par site (pivot / graphe). Réutilisable sur toute instance Odoo.
""",
    'author': 'ADICOPS',
    'website': 'https://odooskills.com',
    'license': 'LGPL-3',
    'depends': ['base', 'mail'],
    'data': [
        'security/affiliate_security.xml',
        'security/ir.model.access.csv',
        'data/affiliate_tag_data.xml',
        'views/affiliate_program_views.xml',
        'views/affiliate_commission_views.xml',
        'views/affiliate_menus.xml',
    ],
    'post_init_hook': 'post_init',
    'application': True,
    'installable': True,
}

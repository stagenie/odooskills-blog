{
    'name': 'OdooSkills - Parcours de lecture du blog',
    'version': '19.0.1.2.0',
    'category': 'Website/Website',
    'summary': "Séries d'articles dans l'ordre de lecture, page /parcours, navigation de série et versions d'Odoo",
    'description': """
Parcours de lecture du blog OdooSkills
======================================
- Séries d'articles ordonnées, rattachées automatiquement par étiquette.
- /parcours : page de choix du profil (une carte par blog ayant une adresse de
  parcours), puis /parcours/<adresse> : page de profil propre à ce blog, avec les
  versions d'Odoo regroupées en onglets (séries « toutes versions » dans chacun).
- Bandeau en tête des listes de blog et repère « étape n/N » dans chaque article de série.
- Navigation « Étape précédente / Étape suivante » générée en bas de chaque article de série
  (le « Read Next » d'Odoo y est masqué ; il reste affiché sur les articles hors série).
- Outil de reprise (tools/markers_apply.py, lancé par odoo-bin shell) : retire des articles
  existants les repères de série écrits à la main (bandeaux numérotés, navigation, listes),
  avec aperçu, sauvegarde et contrôle relu en base.
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

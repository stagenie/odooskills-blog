{
    'name': 'Messagerie — Boîte email unifiée',
    'version': '19.0.2.0.0',
    'category': 'Productivity/Discuss',
    'summary': "Réception IMAP centralisée, réponse, brouillons et tri sans quitter Odoo",
    'description': """
Boîte email unifiée dans Odoo
=============================

Les messages arrivés sur les adresses de la société (support@, ventes@, compta@…)
sont relevés en IMAP et rassemblés dans une file commune, avec leur état de
traitement, leurs pièces jointes et leur contact.

* Répondre depuis la boîte qui a reçu le message, avec sa signature.
* Brouillons persistants, pièces jointes comprises.
* Supprimer ou classer en indésirable jusque sur le serveur IMAP, avec file de
  rattrapage si le serveur ne répond pas.
* Liste de blocage réversible et import de l'historique avec jauge de progression.

Ne dépend que du module « mail » livré avec Odoo Community.
""",
    'author': 'ADICOPS',
    'website': 'https://apps.odooskills.com',
    'support': 'support@odooskills.com',
    'license': 'LGPL-3',
    'images': ['static/description/banner.png'],
    'depends': ['mail'],
    'data': [
        'security/security_groups.xml',
        'security/ir.model.access.csv',
        'security/security_rules.xml',
        'data/ir_cron.xml',
        'views/oski_mail_inbox_views.xml',
        'views/oski_mailbox_views.xml',
        'views/oski_mail_imap_action_views.xml',
        'views/oski_mail_blocklist_views.xml',
        'views/oski_mail_draft_views.xml',
        'views/menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'oski_mail_inbox/static/src/**/*.js',
        ],
    },
    'installable': True,
    'application': True,
}

{
    'name': 'OdooSkills — Industrialiser l\'export XLSX (démo blog)',
    'version': '19.0.1.0.0',
    'category': 'Tools',
    'summary': "Démo d'article : industrialiser un export Excel — assistant de période "
               "(TransientModel), action serveur multi-sélection et envoi planifié par "
               "ir.cron avec pièce jointe e-mail",
    'author': 'OdooSkills',
    'website': 'https://odooskills.com',
    'license': 'LGPL-3',
    'depends': ['sale', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/sales_export_wizard_views.xml',
        'data/ir_actions_server.xml',
        'data/ir_cron.xml',
    ],
    'installable': True,
    'application': False,
}

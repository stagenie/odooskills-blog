{
    'name': 'Messagerie OdooSkills',
    'version': '19.0.1.0.0',
    'category': 'Productivity/Discuss',
    'summary': 'Boîte email unifiée : réception IMAP centralisée et réponse sur place',
    'author': 'ADICOPS',
    'license': 'LGPL-3',
    'depends': ['mail'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_cron.xml',
    ],
    'installable': True,
    'application': True,
}

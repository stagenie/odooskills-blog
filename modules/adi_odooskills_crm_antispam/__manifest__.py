{
    'name': "OdooSkills - CRM Antispam",
    'version': '19.0.1.0.0',
    'category': 'Sales/CRM',
    'summary': "Block spam leads on creation + 1-click 'Mark as SPAM' bulk action",
    'description': """
Auto-archive incoming crm.lead whose email_from is in mail.blacklist.
Provides a server action 'Marquer comme SPAM' bound to the CRM lead list
and form views: blacklists the email and archives all sibling leads from
the same email in one click. Reuses email.validator from
adi_odooskills_email_hygiene for optional manual purge.
""",
    'author': 'ADICOPS',
    'website': 'https://odooskills.com',
    'license': 'LGPL-3',
    'depends': [
        'crm',
        'mail',
        'adi_odooskills_email_hygiene',
    ],
    'data': [
        'data/server_actions.xml',
    ],
    'installable': True,
    'application': False,
}

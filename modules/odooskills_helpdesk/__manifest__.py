{
    'name': 'OdooSkills Helpdesk',
    'version': '19.0.1.16.0',
    'category': 'Services/Helpdesk',
    'summary': 'Module fil rouge du blog OdooSkills — tickets de support',
    'description': """
Module pédagogique construit progressivement à travers les articles techniques
du blog OdooSkills. Étape T23 (fin Bloc 5) : controllers HTTP + API REST —
routes /api/v1/tickets (JSON auth=user) + page publique /helpdesk/status/<ref>.
    """,
    'author': 'OdooSkills',
    'website': 'https://www.odooskills.com',
    'license': 'LGPL-3',
    'depends': ['base', 'mail', 'base_automation', 'website'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence.xml',
        'data/mail_templates.xml',
        'data/automation.xml',
        'report/helpdesk_ticket_report.xml',
        'views/helpdesk_ticket_category_views.xml',
        'views/helpdesk_ticket_views.xml',
        'views/res_partner_views.xml',
        'views/wizard_views.xml',
        'views/ticket_status_templates.xml',
        'views/helpdesk_menus.xml',
    ],
    'installable': True,
    'application': True,
}

{
    'name': 'OdooSkills Helpdesk',
    'version': '19.0.1.19.0',
    'category': 'Services/Helpdesk',
    'summary': 'Module fil rouge du blog OdooSkills — tickets de support',
    'description': """
Module pédagogique construit progressivement à travers les articles techniques
du blog OdooSkills. Étape T26 (Saison Dépassement tech v19) : field widget OWL
custom sla_badge qui affiche le statut SLA avec pastille colorée et icône.
Étape T27 : push bus.bus temps réel — quand sla_status change sur un ticket,
tous les onglets ouverts rafraîchissent la pastille sla_badge via WebSocket
sans rechargement de page.
Étape T28 : helper bench _bench_bulk_escalate pour mesurer le coût réel
du pattern bus.bus sur 10 000 tickets (time.perf_counter, comparaison A/B).
    """,
    'author': 'OdooSkills',
    'website': 'https://www.odooskills.com',
    'license': 'LGPL-3',
    'depends': ['base', 'mail', 'bus', 'base_automation', 'website'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence.xml',
        'data/mail_templates.xml',
        'data/automation.xml',
        'report/helpdesk_ticket_report.xml',
        'views/helpdesk_ticket_category_views.xml',
        'views/helpdesk_ticket_views.xml',
        'views/helpdesk_ticket_views_t26.xml',
        'views/res_partner_views.xml',
        'views/wizard_views.xml',
        'views/ticket_status_templates.xml',
        'views/helpdesk_menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'odooskills_helpdesk/static/src/views/fields/sla_badge/sla_badge.js',
            'odooskills_helpdesk/static/src/views/fields/sla_badge/sla_badge.xml',
            'odooskills_helpdesk/static/src/views/fields/sla_badge/sla_badge.scss',
        ],
    },
    'installable': True,
    'application': True,
}

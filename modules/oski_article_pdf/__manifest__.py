{
    'name': 'OdooSkills - Guides PDF par article',
    'version': '19.0.1.0.0',
    'category': 'Website/Blog',
    'summary': "Génère un guide PDF soigné par article ou par série, livré contre email",
    'author': 'ADICOPS',
    'website': 'https://odooskills.com',
    'license': 'LGPL-3',
    'depends': ['oski_lead_magnet'],
    'data': [
        'security/ir.model.access.csv',
        'views/pdf_templates.xml',
        'data/ir_cron.xml',
        'data/mail_template_pdf.xml',
    ],
    'external_dependencies': {'python': ['weasyprint']},
    'installable': True,
    'application': False,
}

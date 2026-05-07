{
    'name': "OdooSkills - Email Hygiene Validation",
    'version': '19.0.1.0.0',
    'category': 'Marketing/Email Marketing',
    'summary': "Server-side validation of subscriber emails on lead-magnet forms",
    'description': """
Reject unverifiable emails (syntax KO, no MX, disposable, role-based,
DNS timeout) at the /website_mass_mailing/subscribe endpoint.
Logs every rejection with redacted email for RGPD-friendly analytics.
""",
    'author': 'ADICOPS',
    'website': 'https://odooskills.com',
    'license': 'LGPL-3',
    'depends': [
        'website_mass_mailing',
    ],
    'external_dependencies': {
        'python': ['dnspython'],
    },
    'data': [],
    'installable': True,
    'application': False,
}

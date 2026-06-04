{
    'name': "OdooSkills - Google Analytics 4",
    'version': '19.0.1.0.0',
    'category': 'Website/Website',
    'summary': "Inject GA4 gtag.js tracking tag site-wide on odooskills.com",
    'description': """
Adds the Google Analytics 4 gtag.js snippet to the <head> of every public
website page by inheriting website.layout. Measurement ID is stored in
ir.config_parameter (odooskills.ga4_measurement_id) so it can be changed
without touching code. Front-end only — the tag is not injected in the
backend or website editor preview.
""",
    'author': 'ADICOPS',
    'website': 'https://odooskills.com',
    'license': 'LGPL-3',
    'depends': [
        'website',
    ],
    'data': [
        'data/ir_config_parameter.xml',
        'views/website_templates.xml',
    ],
    'installable': True,
    'application': False,
}

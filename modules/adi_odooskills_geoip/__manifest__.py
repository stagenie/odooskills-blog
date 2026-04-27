{
    'name': 'OdooSkills - Lead GeoIP',
    'version': '19.0.1.0.0',
    'category': 'Marketing',
    'summary': "Capture le pays des abonnés newsletter via GeoIP (ip-api.com)",
    'description': """
Ajoute un champ `signup_ip` sur mailing.contact et resout automatiquement
`country_id` via une requete GeoIP a la creation depuis un formulaire web.
Source GeoIP : ip-api.com (gratuit, sans cle, ~45 req/min).
Fallback silencieux si l'appel echoue (timeout 3s, large try/except).
""",
    'author': 'ADICOPS',
    'website': 'https://odooskills.com',
    'license': 'LGPL-3',
    'depends': ['mass_mailing'],
    'data': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}

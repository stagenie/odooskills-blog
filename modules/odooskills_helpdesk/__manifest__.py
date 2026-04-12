{
    'name': 'OdooSkills Helpdesk',
    'version': '19.0.1.0.0',
    'category': 'Services/Helpdesk',
    'summary': 'Module fil rouge du blog OdooSkills — tickets de support',
    'description': """
Module pédagogique construit progressivement à travers les articles techniques
du blog OdooSkills. Étape T08 : modèles de base (Model, TransientModel, AbstractModel).
    """,
    'author': 'OdooSkills',
    'website': 'https://www.odooskills.com',
    'license': 'LGPL-3',
    'depends': ['base', 'mail'],
    'data': [
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'application': True,
}

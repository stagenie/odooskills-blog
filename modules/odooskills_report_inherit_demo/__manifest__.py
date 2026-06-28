{
    'name': 'OdooSkills — Personnalisation rapports PDF (démo xpath)',
    'version': '19.0.1.0.0',
    'category': 'Technical',
    'summary': 'Hérite les rapports PDF standards (facture, devis, achats) via xpath QWeb',
    'description': """
Module fil rouge de l'article « Personnaliser un rapport PDF existant ».
Démontre l'héritage QWeb par xpath sur les rapports standards Odoo 19 :
facture client, devis / pro forma de vente, demande de prix et bon de commande
fournisseur. Aucune surcharge Python : uniquement des vues héritées.
""",
    'author': 'OdooSkills',
    'website': 'https://odooskills.com',
    'license': 'LGPL-3',
    'depends': ['account', 'sale', 'purchase'],
    'data': [
        'report/account_invoice_inherit.xml',
        'report/sale_order_inherit.xml',
        'report/purchase_report_inherit.xml',
    ],
    'installable': True,
    'application': False,
}

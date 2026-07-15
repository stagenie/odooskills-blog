from odoo import fields, models


class TradDemoProduct(models.Model):
    _name = 'trad.demo.product'
    _description = "Produit vitrine (démo traduction)"

    # Champ traduisible : Odoo 19 le stocke en colonne jsonb {"fr_FR": ..., "en_US": ...}
    name = fields.Char(string="Désignation", translate=True, required=True)
    # Texte long également traduisible
    description = fields.Text(string="Description", translate=True)
    # Champ NON traduisible pour contraste (pas de bouton langue)
    reference = fields.Char(string="Référence interne")

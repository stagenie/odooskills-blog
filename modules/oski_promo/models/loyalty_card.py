from odoo import fields, models


class LoyaltyCard(models.Model):
    _inherit = 'loyalty.card'

    # Le champ standard `partner_id` verrouille le code sur un client : Odoo
    # retire le coupon si la commande est au nom d'un autre partenaire. Or un
    # acheteur qui repasse en invité sur la boutique reçoit un nouveau
    # partenaire, même avec la même adresse. Ce champ garde la trace du
    # destinataire du code personnel sans ce verrou : le code reste à usage
    # unique (points), mais n'importe quel panier peut le consommer.
    oski_partner_id = fields.Many2one(
        'res.partner', string='Destinataire du code', index=True, ondelete='set null',
        help="Client à qui ce code personnel a été envoyé. Contrairement au "
             "champ Client, ne restreint pas l'usage du code à ce partenaire.")

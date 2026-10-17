from odoo import api, fields, models
from odoo.exceptions import ValidationError


class LoyaltyReward(models.Model):
    _inherit = 'loyalty.reward'

    # Un code « prix net » promet un montant final (« le pack à 5,90 € »),
    # pas un pourcentage. Odoo calcule les remises en pourcentage du prix
    # de la ligne, donc un −90 % appliqué pendant un prix de lancement
    # descendrait sous le montant promis. Quand ce champ est renseigné,
    # la remise est recalculée pour que les produits visés finissent
    # exactement à ce prix unitaire, quel que soit le prix de liste du jour.
    # Le pourcentage reste affiché à titre indicatif.
    oski_net_price = fields.Monetary(
        string='Prix net garanti',
        currency_field='currency_id',
        help="Prix unitaire final des produits visés après remise, quel que "
             "soit le prix de liste du moment (ne se cumule pas avec une "
             "promotion). Vide : remise standard en pourcentage. Réservé aux "
             "remises sur produits spécifiques.")

    @api.constrains('oski_net_price', 'reward_type', 'discount_applicability', 'discount_mode')
    def _check_oski_net_price(self):
        for reward in self:
            if not reward.oski_net_price:
                continue
            if reward.oski_net_price < 0:
                raise ValidationError("Le prix net garanti ne peut pas être négatif.")
            if (reward.reward_type != 'discount' or reward.discount_applicability != 'specific'
                    or reward.discount_mode != 'percent'):
                raise ValidationError(
                    "Le prix net garanti exige une remise en pourcentage sur des produits spécifiques.")

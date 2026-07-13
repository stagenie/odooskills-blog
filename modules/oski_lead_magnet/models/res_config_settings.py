from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    oski_welcome_percent = fields.Integer(
        string="Remise nouveaux inscrits (%)",
        config_parameter='oski_lead_magnet.welcome_percent', default=30)
    oski_offer_hours = fields.Integer(
        string="Validité de l'offre (heures)",
        config_parameter='oski_lead_magnet.offer_hours', default=72)

    def set_values(self):
        super().set_values()
        pct = int(self.oski_welcome_percent or 30)
        reward = self.env.ref('oski_lead_magnet.welcome_reward', raise_if_not_found=False)
        if reward and reward.discount != pct:
            reward.discount = pct

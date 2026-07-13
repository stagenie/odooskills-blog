from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    oski_offer_enabled = fields.Boolean(
        string="Activer la remise nouveaux inscrits",
        config_parameter='oski_lead_magnet.offer_enabled', default=True)
    oski_welcome_percent = fields.Integer(
        string="Remise nouveaux inscrits (%)",
        config_parameter='oski_lead_magnet.welcome_percent', default=30)
    oski_offer_hours = fields.Integer(
        string="Validité de l'offre (heures)",
        config_parameter='oski_lead_magnet.offer_hours', default=72)

    def set_values(self):
        super().set_values()
        Offer = self.env['oski.welcome.offer']
        pct = Offer._welcome_percent()  # reads the param just written, returns the clamped value
        # persist the clamped value so display surfaces and the real coupon can never diverge
        self.env['ir.config_parameter'].sudo().set_param('oski_lead_magnet.welcome_percent', str(pct))
        reward = self.env.ref('oski_lead_magnet.welcome_reward', raise_if_not_found=False)
        if reward and reward.discount != pct:
            reward.discount = pct

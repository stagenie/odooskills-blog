import secrets
from datetime import timedelta

from odoo import api, fields, models


class OskiWelcomeOffer(models.Model):
    _name = 'oski.welcome.offer'
    _description = "Offre de bienvenue -50% (coupon personnel)"
    _order = 'create_date desc'

    email = fields.Char(required=True, index=True)
    partner_id = fields.Many2one('res.partner', string="Contact", ondelete='set null')
    coupon_id = fields.Many2one('loyalty.card', string="Coupon", ondelete='set null')
    token = fields.Char(index=True, copy=False, readonly=True)
    state = fields.Selection([
        ('dormant', "Dormant"),
        ('active', "Actif"),
        ('used', "Utilisé"),
        ('expired', "Expiré"),
    ], default='dormant', required=True, index=True)
    activated_at = fields.Datetime(readonly=True)
    deadline = fields.Datetime(readonly=True)
    source = fields.Char(help="popup / pdf:<slug>")

    _unique_email = models.Constraint('UNIQUE (email)', "Une seule offre de bienvenue par email.")

    def _offer_hours(self):
        val = self.env['ir.config_parameter'].sudo().get_param('oski_lead_magnet.offer_hours', '72')
        try:
            return int(val)
        except (TypeError, ValueError):
            return 72

    def _create_coupon(self, partner):
        program = self.env.ref('oski_lead_magnet.welcome_program')
        return self.env['loyalty.card'].sudo().create({
            'program_id': program.id,
            'partner_id': partner.id if partner else False,
            'points': 1,
            'code': 'OSK-' + secrets.token_hex(4).upper(),
        })

    @api.model
    def create_for_email(self, email, partner, source):
        email = (email or '').strip().lower()
        existing = self.sudo().search([('email', '=', email)], limit=1)
        if existing:
            return existing
        coupon = self._create_coupon(partner)
        return self.sudo().create({
            'email': email,
            'partner_id': partner.id if partner else False,
            'coupon_id': coupon.id,
            'token': secrets.token_urlsafe(24),
            'source': source,
            'state': 'dormant',
        })

    def activate(self):
        self.ensure_one()
        if self.state != 'dormant':
            return self
        now = fields.Datetime.now()
        self.write({
            'state': 'active',
            'activated_at': now,
            'deadline': now + timedelta(hours=self._offer_hours()),
        })
        return self

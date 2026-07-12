from datetime import timedelta

from odoo import api, fields, models


class OskiLeadAttempt(models.Model):
    _name = 'oski.lead.attempt'
    _description = "Trace anti-abus des soumissions de capture (rate-limit)"

    ip = fields.Char(index=True)

    @api.autovacuum
    def _gc_attempts(self):
        cutoff = fields.Datetime.now() - timedelta(hours=1)
        self.sudo().search([('create_date', '<', cutoff)]).unlink()

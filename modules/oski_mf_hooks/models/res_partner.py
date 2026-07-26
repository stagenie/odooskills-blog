import logging

from odoo import models

_logger = logging.getLogger(__name__)
_logger.warning("HOOK 1bis — chargement du module Python models/res_partner.py")


class ResPartner(models.Model):
    _inherit = 'res.partner'

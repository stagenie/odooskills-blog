import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    _logger.info("pre 0.0.0 : version installée %s, modèle chargé : %s",
                 version, 'oski.parc.materiel' in env.registry)

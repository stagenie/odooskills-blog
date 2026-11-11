import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    # après le chargement du module : l'ORM est là, nouveaux champs compris
    env = api.Environment(cr, SUPERUSER_ID, {})
    prefixe = env['ir.config_parameter'].get_str('oski_parc.prefixe')
    if prefixe:
        env['res.company'].search([]).oski_parc_prefixe = prefixe
    # le format de la référence a changé : recalculer toutes les références stockées
    materiels = env['oski.parc.materiel'].search([])
    env.add_to_compute(materiels._fields['reference'], materiels)
    materiels.flush_recordset(['reference'])
    _logger.info("préfixe %r repris, %s références recalculées", prefixe, len(materiels))

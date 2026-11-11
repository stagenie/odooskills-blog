import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    # tous les modules sont à jour : l'ancien paramètre ne sert plus à personne
    cr.execute("DELETE FROM ir_config_parameter WHERE key = 'oski_parc.prefixe'")
    _logger.info("paramètre oski_parc.prefixe supprimé (%s ligne)", cr.rowcount)

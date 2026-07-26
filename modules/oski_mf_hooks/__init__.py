import logging

from . import models

_logger = logging.getLogger(__name__)


def _post_load():
    _logger.warning("HOOK 1/4 post_load — import du paquet Python, aucun registre")


def _pre_init(env):
    _logger.warning("HOOK 2/4 pre_init_hook — tables du module PAS encore creees")


def _post_init(env):
    count = env['res.partner'].search_count([])
    _logger.warning("HOOK 3/4 post_init_hook — donnees XML chargees, %s partenaires", count)


def _uninstall(env):
    _logger.warning("HOOK 4/4 uninstall_hook — desinstallation en cours")

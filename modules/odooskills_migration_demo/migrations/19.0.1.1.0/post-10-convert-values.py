"""Post-migration 19.0.1.0.0 → 19.0.1.1.0 — convertir valeurs selection.

Exécuté APRÈS que l'ORM ait chargé le modèle. À ce moment-là la colonne
``state`` existe (renommée ou créée). On convertit les valeurs ``'confirm'``/
``'cancel'`` vers ``'confirmed'``/``'cancelled'``.

Pour accéder à env depuis un script de migration, on le construit :
    env = api.Environment(cr, SUPERUSER_ID, {})
"""
import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    _logger.info("T25 migration — post: convert selection values")

    mapping = {'confirm': 'confirmed', 'cancel': 'cancelled'}
    for old, new in mapping.items():
        cr.execute(
            "UPDATE mig_demo_item SET state = %s WHERE state = %s",
            (new, old),
        )
        count = cr.rowcount
        if count:
            _logger.info("  %d record(s) : %s → %s", count, old, new)

    # Exemple d'accès à l'ORM via env (utile si on doit invoquer un compute
    # ou déclencher un recompute sur les enregistrements migrés)
    env = api.Environment(cr, SUPERUSER_ID, {})
    items = env['mig.demo.item'].search([])
    _logger.info("  %d item(s) après migration post-", len(items))

"""End-migration 19.0.1.0.0 → 19.0.1.1.0 — cleanup.

Exécuté une fois TOUS les modules chargés. Moment idéal pour :
- Drop des colonnes/tables temporaires
- Invalidations de cache
- Déclenchement de crons / compute sur toute la base
"""
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    _logger.info("T25 migration — end: cleanup")

    # S'assurer qu'aucune vieille valeur n'a échappé à la conversion post-
    cr.execute(
        "SELECT COUNT(*) FROM mig_demo_item WHERE state IN ('confirm', 'cancel')"
    )
    stale = cr.fetchone()[0]
    if stale:
        _logger.warning(
            "  %d records ont encore une valeur legacy — intervention manuelle",
            stale,
        )
    else:
        _logger.info("  aucune valeur legacy résiduelle — migration propre")

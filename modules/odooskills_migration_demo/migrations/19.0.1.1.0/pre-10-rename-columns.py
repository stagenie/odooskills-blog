"""Pre-migration 19.0.1.0.0 → 19.0.1.1.0 — rename SQL columns.

Exécuté AVANT que l'ORM ne charge le modèle. À ce moment-là la colonne
``state`` n'existe pas encore (l'ORM va la créer). On renomme la vieille
colonne ``legacy_status`` en ``state`` pour que l'ORM la réutilise au lieu
d'en créer une neuve et de perdre les données.

Signature v19 obligatoire : migrate(cr, version).
Paramètres valides : (cr, version) / (cr, _version) / (_cr, version) / (_cr, _version).
Source : odoo/modules/migration.py:223-257 (VALID_MIGRATE_PARAMS).
"""
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    _logger.info("T25 migration — pre: rename columns legacy_* → *")

    # 1. Renommer la colonne selection
    cr.execute("""
        SELECT column_name FROM information_schema.columns
         WHERE table_name = 'mig_demo_item' AND column_name = 'legacy_status'
    """)
    if cr.fetchone():
        cr.execute("ALTER TABLE mig_demo_item RENAME COLUMN legacy_status TO state")
        _logger.info("  legacy_status → state")

    # 2. Renommer la table de liaison Many2many
    cr.execute("""
        SELECT table_name FROM information_schema.tables
         WHERE table_name = 'mig_demo_item_legacy_user_rel'
    """)
    if cr.fetchone():
        cr.execute(
            "ALTER TABLE mig_demo_item_legacy_user_rel "
            "RENAME TO mig_demo_item_res_users_rel"
        )
        _logger.info("  table Many2many renommée")

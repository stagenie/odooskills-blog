import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    # avant le chargement du nouveau code : SQL seulement
    cr.execute("""
        SELECT 1 FROM information_schema.columns
         WHERE table_name = 'oski_parc_materiel' AND column_name = 'numero'
    """)
    if not cr.fetchone():
        return
    cr.execute("ALTER TABLE oski_parc_materiel RENAME COLUMN numero TO numero_serie")
    cr.execute("SELECT count(*) FROM oski_parc_materiel WHERE numero_serie IS NOT NULL")
    _logger.info("colonne numero renommée en numero_serie (%s valeurs gardées)", cr.fetchone()[0])

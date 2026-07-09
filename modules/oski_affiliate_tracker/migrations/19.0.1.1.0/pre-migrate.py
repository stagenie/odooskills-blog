def migrate(cr, version):
    """Le champ `site` passe de Selection à Char (programme + commission).
    On supprime les anciennes options de sélection en base pour éviter
    l'erreur de reconciliation du type de champ (`_process_ondelete`).
    """
    cr.execute("""
        DELETE FROM ir_model_fields_selection s
        USING ir_model_fields f
        WHERE s.field_id = f.id
          AND f.model IN ('oski.affiliate.program', 'oski.affiliate.commission')
          AND f.name = 'site'
    """)

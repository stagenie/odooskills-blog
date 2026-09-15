def _create_company_sequences(env):
    """Les sociétés qui existent déjà à l'installation reçoivent leur séquence."""
    env['res.company'].search([])._odooskills_create_work_order_sequence()

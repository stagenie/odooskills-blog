def post_init(env):
    """Rend l'app visible à tous les utilisateurs internes.
    L'implication XML sur base.group_user ne se propage pas toujours aux
    utilisateurs existants lors d'une mise à jour ; on force ici l'appartenance.
    """
    mgr = env.ref('oski_affiliate_tracker.group_oski_affiliate_manager',
                  raise_if_not_found=False)
    if not mgr:
        return
    gu = env.ref('base.group_user', raise_if_not_found=False)
    if gu:
        gu.write({'implied_ids': [(4, mgr.id)]})
    for user in env['res.users'].search([('share', '=', False)]):
        user.write({'group_ids': [(4, mgr.id)]})

PARCOURS_URL = '/parcours'


def post_init(env):
    _oski_ensure_parcours_menu(env)


def uninstall_hook(env):
    """Retire, sur chaque site, l'entrée de menu « Parcours de lecture » créée par
    post_init : sans elle, le menu garderait un lien mort vers /parcours."""
    env['website.menu'].search([('url', '=', PARCOURS_URL)]).unlink()


def _oski_ensure_parcours_menu(env):
    """Sur chaque site, ajoute « Parcours de lecture » en tête du menu qui regroupe
    les blogs (parent des entrées /blog/…), à défaut au premier niveau. Idempotent."""
    Menu = env['website.menu']
    for website in env['website'].search([]):
        blog_entries = Menu.search([('website_id', '=', website.id), ('url', '=like', '/blog/%')])
        parent = blog_entries.parent_id[:1] or website.menu_id
        if not parent:
            continue
        if Menu.search_count([('parent_id', '=', parent.id), ('url', '=', PARCOURS_URL)]):
            continue
        Menu.create({
            'name': 'Parcours de lecture',
            'url': PARCOURS_URL,
            'parent_id': parent.id,
            'website_id': website.id,
            'sequence': 0,
        })

import logging

_logger = logging.getLogger(__name__)

EXTRACT_LIST_BY_CODE = {
    'E1': 'Extrait E1 — Tech',
    'E2': 'Extrait E2 — Fonctionnel',
    'E3': 'Extrait E3 — Déploiement',
}

# default_code -> (codes ebook, xmlid catégorie tier ou None)
PRODUCT_MAP = {
    'EBOOK-E1': (['E1'], None),
    'EBOOK-E2': (['E2'], None),
    'EBOOK-E3': (['E3'], None),
    'PACK-E1E3': (['E1', 'E3'], 'cat_client_pack'),
    'PACK-E1E2': (['E1', 'E2'], 'cat_client_pack'),
    'PACK-E2E3': (['E2', 'E3'], 'cat_client_pack'),
    'PACK-TRILOGIE': (['E1', 'E2', 'E3'], 'cat_client_trilogie'),
}


def post_init(env):
    """Câble le catalogue existant (créé au runtime par les scripts landing) :
    listes extrait résolues par nom, produits résolus par default_code. Idempotent."""
    Ebook = env['oski.ebook']
    Mlist = env['mailing.list']
    Tmpl = env['product.template']

    # 1) lier les listes extrait par nom
    for code, lname in EXTRACT_LIST_BY_CODE.items():
        ebook = Ebook.search([('code', '=', code)], limit=1)
        if not ebook:
            continue
        mlist = Mlist.search([('name', '=', lname)], limit=1)
        if mlist:
            ebook.extract_list_id = mlist.id
        else:
            _logger.info('post_init: liste extrait "%s" introuvable (ebook %s)', lname, code)

    # 2) lier les produits par default_code
    for default_code, (ebook_codes, tier_xmlid) in PRODUCT_MAP.items():
        tmpl = Tmpl.search([('default_code', '=', default_code)], limit=1)
        if not tmpl:
            _logger.info('post_init: produit %s absent, lien ignoré', default_code)
            continue
        ebooks = Ebook.search([('code', 'in', ebook_codes)])
        vals = {'ebook_ids': [(6, 0, ebooks.ids)]}
        if tier_xmlid:
            tier = env.ref('oski_ebook_lifecycle.%s' % tier_xmlid, raise_if_not_found=False)
            if tier:
                vals['lifecycle_tier_category_id'] = tier.id
        tmpl.write(vals)

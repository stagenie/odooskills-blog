from odoo import models

# Mots-clés (blog name + tags, insensible casse) -> codes produit cibles.
_TECH_KW = ('développ', 'developp', 'technique', 'code', 'python', 'owl', 'orm')
_FUNC_KW = ('fonctionnel', 'gestion', 'métier', 'metier', 'consultant', 'utilisateur')
_DEPLOY_KW = ('déploiement', 'deploiement', 'production', 'serveur', 'devops', 'infra')


class BlogPost(models.Model):
    _inherit = 'blog.post'

    def _get_ebook_cta_products(self):
        """Produits ebook à mettre en avant en fin d'article, selon le blog + tags.

        Retourne un product.template recordset (≤3, dédupliqué).
        Défaut : Trilogie si aucun mot-clé ne correspond.
        """
        self.ensure_one()

        haystack = ' '.join([
            self.blog_id.name or '',
            ' '.join(self.tag_ids.mapped('name')),
        ]).lower()

        codes = []
        if any(k in haystack for k in _TECH_KW):
            codes += ['EBOOK-E1', 'EBOOK-E3']
        if any(k in haystack for k in _DEPLOY_KW):
            codes.append('EBOOK-E3')
        if any(k in haystack for k in _FUNC_KW):
            codes.append('EBOOK-E2')

        # Dédup en préservant l'ordre d'insertion
        seen, ordered = set(), []
        for c in codes:
            if c not in seen:
                seen.add(c)
                ordered.append(c)

        if not ordered:
            ordered = ['PACK-TRILOGIE']

        Tmpl = self.env['product.template']
        prods = Tmpl
        for c in ordered:
            p = Tmpl.search([('default_code', '=', c), ('is_published', '=', True)], limit=1)
            if p:
                prods |= p
        return prods

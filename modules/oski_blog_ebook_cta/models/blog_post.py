import re

from odoo import models

# Mots-clés (titre + blog name + tags + série, insensible casse) -> famille de livre.
_TECH_KW = ('développ', 'developp', 'technique', 'code', 'python', 'owl', 'orm')
_FUNC_KW = ('fonctionnel', 'gestion', 'métier', 'metier', 'consultant', 'utilisateur')
_DEPLOY_KW = ('déploiement', 'deploiement', 'production', 'serveur', 'devops', 'infra')
_REPORT_KW = ('rapport', 'excel', 'xlsx', 'tableur', 'état', 'etat', 'analyse', ' sql')

# Un article écrit pour Odoo 19 (titre, blog, tags ou série qui le disent) garde
# le CTA de l'édition 19 ; tout le reste propose l'édition courante.
_ODOO19_RE = re.compile(r'odoo\s*19|\bv19\b|\b19\.0\b', re.IGNORECASE)

# Codes produit par édition. L'édition 20 est la référence ; la 19 sert aux
# articles qui la ciblent et de repli tant que la gamme 20 n'est pas publiée.
_CODES = {
    '20': {'tech': 'EBOOK-E1-20', 'deploy': 'EBOOK-E3-20', 'func': 'EBOOK-E2-20',
           'report': None, 'pack': 'PACK-ODOO20'},
    '19': {'tech': 'EBOOK-E1', 'deploy': 'EBOOK-E3', 'func': 'EBOOK-E2',
           'report': 'EBOOK-E5', 'pack': 'PACK-TRILOGIE'},
}


class BlogPost(models.Model):
    _inherit = 'blog.post'

    def _get_ebook_cta_haystack(self):
        self.ensure_one()
        return ' '.join([
            self.name or '',
            self.blog_id.name or '',
            ' '.join(self.tag_ids.mapped('name')),
            (self.series_id.name or '') if 'series_id' in self._fields and self.series_id else '',
        ]).lower()

    def _get_ebook_cta_edition(self):
        """'19' pour un article qui cible Odoo 19, '20' sinon."""
        self.ensure_one()
        return '19' if _ODOO19_RE.search(self._get_ebook_cta_haystack()) else '20'

    def _get_ebook_cta_families(self):
        """Familles de livres à proposer, dans l'ordre, selon blog + tags + titre."""
        haystack = self._get_ebook_cta_haystack()
        families = []
        if any(k in haystack for k in _REPORT_KW):
            families.append('report')
        if any(k in haystack for k in _TECH_KW):
            families += ['tech', 'deploy']
        if any(k in haystack for k in _DEPLOY_KW):
            families.append('deploy')
        if any(k in haystack for k in _FUNC_KW):
            families.append('func')
        seen, ordered = set(), []
        for f in families:
            if f not in seen:
                seen.add(f)
                ordered.append(f)
        return ordered[:3] or ['pack']

    def _get_ebook_cta_products_for(self, edition):
        Tmpl = self.env['product.template']
        prods = Tmpl
        for fam in self._get_ebook_cta_families():
            code = _CODES[edition].get(fam)
            if not code:
                continue
            p = Tmpl.search([('default_code', '=', code), ('is_published', '=', True)], limit=1)
            if p:
                prods |= p
        return prods

    def _get_ebook_cta_products(self):
        """Produits ebook à mettre en avant en fin d'article (≤3, dédupliqués).

        Édition 20 par défaut ; édition 19 pour les articles qui la ciblent.
        Repli sur la 19 tant qu'aucun produit 20 n'est publié (avant le lancement).
        """
        self.ensure_one()
        edition = self._get_ebook_cta_edition()
        prods = self._get_ebook_cta_products_for(edition)
        if not prods and edition == '20':
            prods = self._get_ebook_cta_products_for('19')
        return prods

    def _get_ebook_cta_edition_20_available(self):
        """Pour un article Odoo 19 : la gamme 20 est-elle en vente ? (ligne « Édition Odoo 20 disponible »)."""
        self.ensure_one()
        if self._get_ebook_cta_edition() != '19':
            return False
        return bool(self.env['product.template'].search(
            [('default_code', '=', _CODES['20']['pack']), ('is_published', '=', True)], limit=1))

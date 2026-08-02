import re

from lxml import etree

from odoo import api, fields, models


class Website(models.Model):
    _inherit = 'website'

    @api.model
    def oski_price(self, sku):
        """Point d'entrée unique des templates. Tolérant : une référence
        inconnue rend un dict neutre plutôt qu'une page en erreur."""
        produit = self.env['product.template'].sudo().search(
            [('default_code', '=', sku)], limit=1)
        if not produit:
            return {'barre': 0.0, 'payer': 0.0, 'after': 0.0,
                    'barre_fmt': '', 'payer_fmt': '', 'after_fmt': '',
                    'promo': False, 'deadline_iso': '', 'label': '',
                    'found': False}
        info = produit._oski_price_info()
        info['found'] = True
        return info

    @api.model
    def oski_running_campaign(self):
        """Campagne en cours, tous produits confondus : alimente le bandeau."""
        now = fields.Datetime.now()
        return self.env['oski.promo.campaign'].sudo().search([
            ('applied', '=', True), ('active', '=', True),
            ('date_start', '<=', now), ('date_end', '>=', now),
        ], limit=1)

    # Un montant suivi d'un symbole euro, avec ou sans décimales.
    _OSKI_PRICE_RE = re.compile(
        r'(?<![\d,.])(\d{1,4}(?:[,.]\d{2})?)\s*(?:\xa0|&nbsp;)?\s*€')

    @api.model
    def oski_scan_hardcoded_prices(self):
        """Prix écrits en dur dans les pages, hors bloc tarif.

        Ne bloque rien : rend une liste de signalements. Une régression
        silencieuse devient une régression visible.
        """
        signalements = []
        pages = self.env['website.page'].sudo().search([])
        for page in pages:
            arch = page.view_id.arch or ''
            if not arch.strip():
                continue
            try:
                arbre = etree.fromstring(arch)
            except etree.XMLSyntaxError:
                continue
            # Les blocs tarif sont dynamiques : leur contenu n'est pas une dette.
            for noeud in arbre.xpath('//*[@data-oski-price]'):
                noeud.getparent().remove(noeud)
            texte = ' '.join(etree.tostring(
                arbre, encoding='unicode', method='text').split())
            for trouve in self._OSKI_PRICE_RE.finditer(texte):
                debut = max(0, trouve.start() - 60)
                signalements.append({
                    'page_id': page.id,
                    'url': page.url,
                    'value': trouve.group(1),
                    'excerpt': texte[debut:trouve.end() + 20],
                })
        return signalements

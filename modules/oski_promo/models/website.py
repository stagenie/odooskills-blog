import logging
import re
from datetime import timedelta

from lxml import etree

from odoo import api, fields, models

_logger = logging.getLogger(__name__)

# Séparateurs de milliers rencontrés dans les pages : espace normale,
# insécable (U+00A0), insécable fine (U+202F), fine (U+2009). Sans eux,
# « 1 500 € » n'est lu que comme « 500 » — le lookbehind ne franchit pas
# l'espace et seul le dernier groupe de chiffres est capturé.
_OSKI_ESPACE_MILLIERS = '[ \\u00a0\\u202f\\u2009]'

# Blanc admis entre le montant et sa marque monétaire. Volontairement sans
# saut de ligne : « Chapitre 3 \n Euro… » n'est pas un prix.
_OSKI_BLANC = r'(?:&nbsp;|[ \t\u00a0\u202f\u2009])*'

#: Un montant figé : chiffres suivis d'une marque monétaire, soit le
#: symbole €, soit la forme littérale euro/euros/EUR (insensible à la
#: casse) — un rédacteur écrit aussi naturellement « 24 euros » que
#: « 24 € ». Une ou deux décimales, séparateur de milliers lu en entier.
#:
#: Motif UNIQUE du chantier : le détecteur de production et le garde-fou
#: des tests doivent parler du même filet, sinon le quitus « liste vide »
#: est mensonger. Les tests l'IMPORTENT, ils ne le recopient pas.
#:
#: Faux amis tenus dehors : « meilleur », « heure », « leur »,
#: « européens », « 14 heures » — l'exigence d'un chiffre en tête écarte
#: les trois premiers, le \b final écarte « européens », et « heures »
#: ne commence par aucune des marques.
OSKI_PRICE_RE = re.compile(
    r'(?<![\d,.])'
    r'(\d{1,3}(?:' + _OSKI_ESPACE_MILLIERS + r'\d{3})+(?:[,.]\d{1,2})?'
    r'|\d{1,4}(?:[,.]\d{1,2})?)'
    + _OSKI_BLANC +
    r'(?:€|euros?\b|eur\b)',
    re.IGNORECASE)


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
    def oski_catalogue(self):
        """Les produits ebook publiés, séparés en unités et en packs.

        Point d'entrée du hub /formations, qui se construisait jusqu'ici
        carte par carte dans l'arch : ajouter un ebook demandait d'éditer
        une vue, et chaque édition réintroduisait des prix figés.

        Aucun filtre sur les champs de présentation : un produit publié
        apparaît toujours, quitte à retomber sur son nom et sa fiche
        boutique. Un oubli de présentation doit se voir à l'écran, pas
        faire disparaître un produit qu'on vend.

        L'ordre est celui de la boutique (`website_sequence`) : une seule
        notion d'ordre pour toutes les surfaces.
        """
        produits = self.env['product.template'].sudo().search(
            [('ebook_ids', '!=', False), ('website_published', '=', True)],
            order='website_sequence, id')
        return {
            'monos': produits.filtered(lambda p: not p.oski_is_pack),
            'packs': produits.filtered(lambda p: p.oski_is_pack),
        }

    #: Horizon de validité annoncé aux moteurs de recherche hors campagne.
    #: Une date lointaine écrite en dur finirait par être dépassée sans que
    #: personne ne s'en aperçoive — c'est exactement ce qui s'est produit
    #: sur deux landings, dont le `priceValidUntil` était périmé depuis un
    #: mois. Une durée glissante ne peut pas pourrir.
    OSKI_VALIDITE_JOURS = 180

    @api.model
    def oski_price_valid_until(self):
        """Date jusqu'à laquelle le prix affiché est annoncé valable, au
        format ISO court attendu par schema.org.

        Pendant une campagne, c'est son échéance : au-delà, le prix change
        et l'annonce ne vaut plus. Hors campagne, un horizon glissant.
        """
        campagne = self.oski_running_campaign()
        if campagne:
            return fields.Date.to_string(campagne.date_end.date())
        horizon = fields.Date.context_today(self) + timedelta(
            days=self.OSKI_VALIDITE_JOURS)
        return fields.Date.to_string(horizon)

    @api.model
    def oski_running_campaign(self):
        """Campagne en cours, tous produits confondus : alimente le bandeau.

        Une campagne dont les items de liste de prix ont été écrasés (voir
        product_template._oski_promo_effective) n'est pas en cours : elle
        est marquée `applied` mais n'accorde plus rien. Le bandeau doit
        alors disparaître au même titre que le compteur — annoncer une
        remise pendant que la caisse encaisse le plein tarif est le seul
        défaut que ce module ne peut pas se permettre.
        """
        now = fields.Datetime.now()
        campagnes = self.env['oski.promo.campaign'].sudo().search([
            ('applied', '=', True), ('active', '=', True),
            ('date_start', '<=', now), ('date_end', '>=', now),
        ])
        for campagne in campagnes:
            if campagne._oski_effective():
                return campagne
        return self.env['oski.promo.campaign'].sudo().browse()

    # Attributs des blocs tarif dynamiques (oski_promo.price_block) : leur
    # valeur n'est pas une dette, elle est recalculée à chaque rendu par
    # oski_price(). Ne jamais les signaler — même logique d'exclusion que
    # pour le texte du bloc, qui est déjà retiré de l'arbre ci-dessous.
    _OSKI_ATTRS_DYNAMIQUES = frozenset((
        'data-oski-price', 'data-after', 'data-barre', 'data-after-value',
    ))

    @api.model
    def oski_scan_hardcoded_prices(self):
        """Prix écrits en dur dans les pages, hors bloc tarif.

        Scanne deux canaux : le texte des nœuds et leurs attributs. Un prix
        porté par un attribut (ex. data-price-regular, data-r) est invisible
        au rendu textuel mais réécrit le DOM au même titre qu'un prix en
        clair — souvent réécrit par un script JS toutes les secondes, ce qui
        rend une conversion partielle (texte seul) inopérante en silence.

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
                # Les blocs tarif sont dynamiques : leur contenu n'est pas
                # une dette. On réattache le texte qui les suit (.tail)
                # avant de les retirer, sinon lxml l'emporte avec le nœud.
                for noeud in arbre.xpath('//*[@data-oski-price]'):
                    parent = noeud.getparent()
                    if parent is None:
                        continue
                    if noeud.tail:
                        precedent = noeud.getprevious()
                        if precedent is not None:
                            precedent.tail = (
                                (precedent.tail or '') + noeud.tail)
                        else:
                            parent.text = (parent.text or '') + noeud.tail
                    parent.remove(noeud)
                texte = ' '.join(etree.tostring(
                    arbre, encoding='unicode', method='text').split())
            except Exception as exc:
                # Une page illisible ne doit pas faire taire le scan des
                # autres : on le signale et on continue.
                _logger.warning(
                    "oski_scan_hardcoded_prices : page %s ignorée (%s)",
                    page.url, exc)
                continue
            for trouve in OSKI_PRICE_RE.finditer(texte):
                debut = max(0, trouve.start() - 60)
                signalements.append({
                    'page_id': page.id,
                    'url': page.url,
                    'value': trouve.group(1),
                    'excerpt': texte[debut:trouve.end() + 20],
                    'channel': 'texte',
                })
            # Canal attribut : les blocs tarif dynamiques ont déjà été
            # retirés de l'arbre ci-dessus, mais on exclut explicitement
            # leurs attributs par nom pour rester correct si un jour un
            # attribut dynamique apparaît sur un nœud non retiré.
            for noeud in arbre.iter():
                for nom_attr, valeur_attr in noeud.attrib.items():
                    if nom_attr in self._OSKI_ATTRS_DYNAMIQUES:
                        continue
                    for trouve in OSKI_PRICE_RE.finditer(valeur_attr):
                        signalements.append({
                            'page_id': page.id,
                            'url': page.url,
                            'value': trouve.group(1),
                            'excerpt': '%s=%s' % (nom_attr, valeur_attr),
                            'channel': 'attribut',
                        })
        return signalements

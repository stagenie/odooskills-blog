# oski_promo — promotions dynamiques OdooSkills

## Lancer une promotion

1. Site Web → Promotions OdooSkills → Nouveau. *(Entrée réservée aux
   administrateurs système : c'est le seul groupe auquel l'ACL du modèle
   accorde l'accès.)*
2. Renseigner le nom interne, le **libellé public** (affiché sur le site),
   les dates de début et de fin, la remise en pourcentage.
3. « Générer les lignes », puis ajuster les prix produit par produit si besoin.
4. « Appliquer ».

Aucun redémarrage n'est nécessaire : appliquer une campagne n'écrit que des
`product.pricelist.item`, jamais un `arch` de vue. Le rendu suivant est déjà
à jour. Le `systemctl restart odoo19` n'est requis qu'à l'**installation** ou
à la **mise à jour du module** — c'est-à-dire quand un `arch` change. En faire
un rituel de fin de campagne masque les vrais problèmes de cache au lieu de
les révéler.

## Terminer une promotion

Rien à faire. À la date de fin, les items de liste de prix promotionnels
cessent d'être actifs, le repli au prix courant prend la main, et le rendu
ne produit plus ni bandeau ni compteur.

Il n'y a **aucun cron** dans ce module, et il ne faut pas en ajouter : une
tâche planifiée est une pièce mobile qui peut échouer en silence — c'est
précisément ce qui s'est produit le 2 août 2026.

## ⚠️ Ne jamais rejouer la tarification du module lifecycle pendant une campagne

`oski_promo` et `oski_ebook_lifecycle` écrivent **le même espace d'items de
liste de prix**, avec la même clé (`pricelist_id` + `product_tmpl_id`) et la
même purge préalable. Ils ne se connaissent pas.

Concrètement : pendant une campagne appliquée, le checker
`oski_pricing_incoherences()` du module lifecycle passe au rouge sur chaque
produit de la campagne — c'est **attendu**, ce n'est pas une anomalie à
corriger. Le remède habituel (rejouer `pricing_offers.py`, qui appelle
`_oski_apply_pricing_offer()`) **supprimerait les items de la campagne** et
réinstallerait le prix de lancement, sans rien écrire côté campagne.

Pour changer les prix pendant qu'une campagne tourne :

1. « Annuler la campagne » sur la campagne en cours ;
2. faire la modification tarifaire (script lifecycle inclus) ;
3. régénérer les lignes et « Appliquer » de nouveau.

Le module se défend seul contre le cas où la consigne n'est pas suivie :
bandeau, libellé et compte à rebours sont pilotés par le **prix réellement
appliqué**, pas par le booléen `applied`. Si les items promotionnels
disparaissent, l'affichage redevient honnête tout seul — plus de promotion
annoncée au-dessus d'un plein tarif. C'est un filet, pas une autorisation.

## Ajouter une formation

1. Créer le produit, l'`oski.ebook`, lier `ebook_ids`, saisir le prix
   régulier (barré) et le prix courant.
2. **Estamper les emplacements natifs** — sans quoi le produit neuf n'a
   aucun item de liste de prix :

   ```python
   env['product.template'].browse(ID)._oski_apply_pricing_offer()
   ```

   Tant que cet appel n'a pas eu lieu, `_get_product_price` retombe sur
   `list_price`, qui est exprimé en DZD et converti par le **taux de change
   de la devise**, pas par le taux métier `oski.pricing.dzd_rate`. Le bloc
   tarif d'une landing neuve afficherait alors un montant faux.
3. Créer la page de vente en dupliquant `oski_promo.landing_skeleton`.
4. Poser `<t t-set="sku" t-value="'EBOOK-E4'"/>` en tête de la page.

**Ne jamais écrire de montant dans une page.** Chaque prix passe par
`<t t-call="oski_promo.price_block"/>`.

## Contrôler qu'aucun prix n'a été figé

```python
env['website'].oski_scan_hardcoded_prices()
```

Rend la liste des montants écrits en dur dans les pages, hors bloc tarif.
Attendu : liste vide.

Le motif de détection est **unique** et vit dans
`models/website.py` (`OSKI_PRICE_RE`) : les tests l'importent au lieu de le
recopier, faute de quoi le quitus « liste vide » finirait par ne plus rien
garantir. Il couvre le symbole `€`, les formes littérales `euro` / `euros` /
`EUR` insensibles à la casse, une ou deux décimales, et les séparateurs de
milliers (espace normale, insécable, insécable fine) lus en entier.

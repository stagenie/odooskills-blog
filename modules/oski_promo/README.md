# oski_promo — promotions dynamiques OdooSkills

## Lancer une promotion

1. Configuration du site → Promotions OdooSkills → Nouveau.
2. Renseigner le nom interne, le **libellé public** (affiché sur le site),
   les dates de début et de fin, la remise en pourcentage.
3. « Générer les lignes », puis ajuster les prix produit par produit si besoin.
4. « Appliquer ».
5. `systemctl restart odoo19` sur la production.

## Terminer une promotion

Rien à faire. À la date de fin, les items de liste de prix promotionnels
cessent d'être actifs, le repli au prix courant prend la main, et le rendu
ne produit plus ni bandeau ni compteur.

Il n'y a **aucun cron** dans ce module, et il ne faut pas en ajouter : une
tâche planifiée est une pièce mobile qui peut échouer en silence — c'est
précisément ce qui s'est produit le 2 août 2026.

## Ajouter une formation

1. Créer le produit, l'`oski.ebook`, lier `ebook_ids`, saisir le prix
   régulier (barré) et le prix courant.
2. Créer la page de vente en dupliquant `oski_promo.landing_skeleton`.
3. Poser `<t t-set="sku" t-value="'EBOOK-E4'"/>` en tête de la page.

**Ne jamais écrire de montant dans une page.** Chaque prix passe par
`<t t-call="oski_promo.price_block"/>`.

## Contrôler qu'aucun prix n'a été figé

```python
env['website'].oski_scan_hardcoded_prices()
```

Rend la liste des montants écrits en dur dans les pages, hors bloc tarif.
Attendu : liste vide.

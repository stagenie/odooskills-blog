# Bannières des rubriques du blog

Une bannière par rubrique (`blog.blog.cover_properties` → `/web/image/<id>`).

| Source | PNG | Pièce jointe en prod | Rubrique |
|---|---|---|---|
| `fonctionnel-odoo.html` | 1920×700 | 1011 | Fonctionnel Odoo |
| `developpement-odoo.html` | 1920×700 | 1012 | Développement Odoo |
| `radar-odoo.html` | 1920×600 | 1015 | Radar Odoo |
| `la-bibliotheque.html` | 1920×600 | 1016 | Ressources Odoo |

## La contrainte à connaître

Le blog affiche ces images dans un conteneur de **380 px de haut, quelle que soit
la largeur de l'écran**, en `background-size: cover` centré. L'image est donc
rognée verticalement, et d'autant plus que l'écran est large :

- en 1440 px, on voit environ 490 px de la source ;
- en **1920 px, on n'en voit que 380** — c'est le cas le plus serré.

**Tout ce qui compte doit tenir dans les 380 px centraux de la source**, sinon
c'est coupé sur les grands écrans. C'est ce qui rognait la pastille de série et
la bande de bas de page des versions précédentes.

`_check_overlap.py` vérifie cette bande automatiquement ; `_check_crop.py` rend
chaque bannière telle que le site l'affichera, en 1440 et 1920, pour contrôle à l'œil.

## Règles de contenu

- **Aucun numéro de version** : les rubriques sont intemporelles (Odoo 20, puis 21…).
  Pas de « Odoo 19 » dans un titre, une tranche de livre ou un cadran radar.
- **Aucun compteur** (« 50+ articles », « 10 saisons ») : ça vieillit.
- Accents obligatoires — les premières versions en étaient dépourvues.

## Produire et déployer

```bash
# rendu des 4 PNG (venv avec playwright + pillow)
/home/stadev/vscode-projects/odoo19-dev/venv/bin/python _capture.py
/home/stadev/vscode-projects/odoo19-dev/venv/bin/python _check_overlap.py   # bloquant
/home/stadev/vscode-projects/odoo19-dev/venv/bin/python _check_crop.py      # contrôle visuel
```

Déploiement : `tools/blog/covers_blogs_replace.py` remplace le contenu des
pièces jointes **sans changer leur id** — les `cover_properties` restent valides.
Les images sont servies en `no-cache` : le remplacement est visible tout de suite.

# Lead magnets — guides gratuits OdooSkills

Deux guides PDF, offerts en échange d'une inscription sur odooskills.com, livrés par email
(templates 39 / 40) et téléchargeables depuis les pages merci.

| Guide | Fichier courant | Page de capture | Liste | Pièce jointe prod |
|---|---|---|---|---|
| *Odoo 20 : décider et démarrer* (fonctionnel, 31 p.) | `guide-odoo-20-v1.pdf` | `/guide-odoo` | 3 | 1585 |
| *Odoo 20 pour développeurs : votre premier module* (technique, 34 p.) | `guide-technique-odoo-20-v1.pdf` | `/guide-technique-odoo` | 4 | 1586 |

## Sources

- Texte : `content/ebooks/gratuits/guide-fonc-20/` et `guide-tech-20/` (dépôt ebooks).
- Construction : `cd toolbox && make book-qa EBOOK=<livre> && make pdf EBOOK=<livre>`
  (`LAB_REF=ch02` pour le guide technique : son code est vérifié au tag `ch02` de `stagenie/labo-horizon`).
- Pages et emails : `content/blog/pages/leadmagnet/` ; mise en prod : `scripts/odooskills/25_refresh_leadmagnet_pages.py`.

## Versions

| Fichier | Date | Notes |
|---|---|---|
| `guide-odoo-20-v1.pdf` | 2026-10 | Odoo 20, chaîne ebook, captures réelles |
| `guide-technique-odoo-20-v1.pdf` | 2026-10 | Odoo 20, fil rouge Labo Horizon |
| `odooskills-guide-2026-v3.pdf` | 2026-04 | Archive — Odoo 18 & 19 (ReportLab) |
| `guide-technique-odoo19-v1.pdf` | 2026-04 | Archive — Odoo 19 (ReportLab) |

## Mise à jour d'un guide

1. Modifier les sources, reconstruire, relire (`qa-final-*`).
2. Copier le PDF ici en `-vN+1`, mettre à jour ce tableau.
3. Reconstruire pages et emails (`build_pages.py` : nombre de pages et sommaire sont relus dans le PDF), puis relancer le script 25.

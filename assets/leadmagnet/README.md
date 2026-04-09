# Lead Magnet — Guide Express Odoo

## Document

**Fichier** : `odooskills-guide-2026-v3.pdf`
**Titre** : *Odoo, Une Vraie Opportunité pour les Entreprises et les Développeurs*
**Sous-titre** : Découvrez comment la solution Odoo facilite la transformation digitale des entreprises
**Auteur** : BENHAMIDA Mustapha
**Édition** : 2026 — Odoo 18 & 19
**Pages** : 18
**Format** : PDF

## Sommaire (11 chapitres)

| # | Chapitre | Page |
|---|----------|------|
| 01 | À propos de l'auteur | 03 |
| 02 | Pourquoi Odoo en 2026 ? | 04 |
| 03 | Architecture technique d'Odoo | 06 |
| 04 | Community vs Enterprise | 08 |
| 05 | Démarrer avec Odoo — les méthodes modernes | 09 |
| 06 | Avantages pour les entreprises | 11 |
| 07 | Avantages pour les développeurs | 12 |
| 08 | Checklist : vos 7 premières étapes | 14 |
| 09 | Odoo en action : cas d'usage concrets | 15 |
| 10 | Glossaire des termes Odoo | 17 |
| 11 | Pour aller plus loin | 18 |

## Usage

Ce PDF est le **lead magnet** distribué en échange d'une adresse email sur le blog odooskills.com.

### Page de capture (à créer sur le nouveau VPS)

URL cible : `/guide-odoo`

Cette page doit contenir :
1. Visuel de couverture (page 1 du PDF)
2. Pitch (titre + sous-titre)
3. Liste des bénéfices (extraits du sommaire)
4. **Formulaire de capture email** (Odoo Website > Forms)
5. Téléchargement automatique du PDF après soumission
6. Confirmation par email avec lien vers le PDF

### Redirection 301

Toutes les anciennes URLs pointant vers le téléchargement direct doivent rediriger vers cette page de capture :

```nginx
rewrite ^/telecharger-gratuitement-votre-guide-odoo.html$ /guide-odoo permanent;
```

## Trafic actuel (référence)

D'après GA4 (1er janv → 8 avril 2026, 3,3 mois) :
- **TOP 5** des pages les plus vues
- **223 vues** (~67/mois)
- Indique un fort intérêt pour le contenu, à exploiter via la nouvelle page de capture

## Articles liés

Le contenu du PDF chevauche plusieurs articles cibles du blog. Le PDF peut servir de **référence** lors de la rédaction de :

- `odoo-pour-les-entreprises-pourquoi` ↔ Chapitre 02 + 06 du PDF
- `architecture-technique-odoo-19` ↔ Chapitre 03 du PDF
- `odoo-enterprise-vs-community` ↔ Chapitre 04 du PDF
- `installer-odoo-19-*` ↔ Chapitre 05 + 08 du PDF
- `avantages-odoo-developpeurs` ↔ Chapitre 07 du PDF

## Versions

| Version | Date | Notes |
|---------|------|-------|
| v3 | 2026-04 | Édition courante (Odoo 18 & 19) |
| v2 | n/a | Édition antérieure (non archivée) |
| v1 | n/a | Édition originale (non archivée) |

## Workflow de mise à jour

Quand une nouvelle version du guide est produite :
1. Renommer `odooskills-guide-2026-v3.pdf` → `odooskills-guide-2026-vN.pdf`
2. Mettre à jour ce README (versions, sommaire si besoin)
3. Mettre à jour le lien sur la page de capture du VPS
4. Commit : `assets(leadmagnet): release v<N>`

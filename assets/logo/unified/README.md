# Logo du groupe — OdooSkills × AISkillsPro

Marque **mère**, pour la société unique qui porte les deux blogs et la boutique
d'applications. Les logos d'OdooSkills et d'AISkillsPro **ne changent pas** : ils
restent les marques des deux produits. Ce logo-ci les surplombe.

Fichiers identiques dans les deux dépôts :
`ai-blog/branding/unified/` et `content/blog/assets/logo/unified/`.

---

## L'idée

Chaque enfant détient une moitié de l'instrument.

| Élément | Provenance | Ce qu'il dit |
|---|---|---|
| Anneau épais | Le « O » d'ODOO, logo OdooSkills | le métier, la matière, l'anneau qu'on ne rompt pas |
| Aiguille bicolore + pivot | Logo AISkillsPro | la direction |
| Losange plein | Logo AISkillsPro | l'objectif visé |
| Encoche unique au nord-est | **nouveau** | l'aiguille sort de l'anneau : l'IA prolonge le métier, elle ne le remplace pas |

L'encoche est un couloir **droit**, à largeur constante. Une brèche angulaire
s'évaserait vers l'extérieur et l'anneau cesserait de se lire comme un « O ».

L'aiguille **ne touche jamais** le losange : elle vise, elle n'atteint pas.
Le losange déborde du cadre de l'anneau en haut à droite ; ce débordement est
volontaire, ne le recadrez pas au carré (sauf icône, voir plus bas).

---

## Couleurs

| Jeton | Valeur | Emploi |
|---|---|---|
| Encre | `#101F38` | mot-symbole, contrepoids de l'aiguille |
| Teal | `#017E84` | anneau — valeur exacte du logo OdooSkills en production |
| Or | `#F9C846` → `#FFD25A` | aiguille nord + losange — valeur exacte du logo AISkillsPro |
| Ardoise | `#3E5566` | sous-titre (7,9:1 sur blanc) |
| Papier | `#F8F9FA` | pivot |

Deux accents, un par enfant. **Ne pas en ajouter un troisième.**

---

## Typographie

Manrope — la police d'AISkillsPro, dont la graisse 800 tient aussi le « SKILLS »
d'OdooSkills. Mot-symbole en 800, approche `+0.02 em` ; sous-titre en 600,
approche `+0.10 em`. Le filet entre les deux reprend celui du logo OdooSkills.

**Les textes sont vectorisés** : les SVG ne dépendent d'aucune police installée.

---

## Quel fichier prendre

| Situation | Fichier |
|---|---|
| Fond clair | `logo-horizontal-color.svg` |
| Fond sombre (`#0A1628`, `#101F38`) | `logo-horizontal-dark.svg` |
| Format carré, colonne étroite | `logo-vertical-*.svg` |
| Une seule couleur (tampon, gravure, fax) | `logo-*-mono-ink.svg` / `-mono-white.svg` |
| Sans texte | `mark-*.svg` |
| Favicon, icône d'app, avatar | `icon-compact-*.svg`, `png/favicon-*.png` |

`icon-compact-*` n'est **pas** la marque réduite : l'aiguille y est épaissie, le
losange agrandi, l'encoche élargie. En dessous de 48 px la marque détaillée
s'efface au rééchantillonnage. Ne générez jamais un favicon depuis `mark-*.svg`.

## Règles

- Aire de protection : la moitié du diamètre de l'anneau sur les quatre côtés.
- Taille minimale : 96 px de large pour le lockup horizontal, 24 px pour l'icône compacte.
- Ne pas faire pivoter, incliner, étirer, ni changer l'azimut de l'aiguille (30°).
- Ne pas poser la variante `color` sur un fond de teinte moyenne : le pivot clair y flotte.
- Le vide central de l'anneau est un **détourage**, pas un disque blanc : il doit laisser voir le fond.

---

## Régénérer

```bash
python3 scripts/branding/build_unified_logo.py
```

Le script écrit dans les deux dépôts d'un coup. Le mot-symbole et le sous-titre
sont deux constantes en tête de fichier (`WORDMARK`, `SUBLINE`) : si la raison
sociale retenue diffère de « SKILLS », changez la ligne et relancez.

Dépendances : `fonttools`, `cairosvg`, et `scripts/branding/Manrope-var.ttf`
(Manrope, SIL Open Font License 1.1).

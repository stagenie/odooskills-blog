# OdooSkills - Blog

Repository de production des articles, modules de démonstration et captures d'écran du blog **odooskills.com**.

> Branche `19.0` → contenu Odoo 19 (publication courante)
> Branche `18.0` → contenu Odoo 18 (legacy / migrations)

## Auteur

**BENHAMIDA Mustapha** — Consultant technico-fonctionnel Odoo, 10+ ans d'expérience.
Fondateur d'**ADICOPS** (consulting SI, 2018) et du blog **OdooSkills**.

Contact : info@odooskills.com

## Structure du repo

```
odooskills-blog/
├── articles/                ← Sources Markdown des articles publiés/en cours
│   └── <slug>.md
├── modules/                 ← Modules Odoo de démonstration testés (par article technique)
│   └── <slug>/
│       └── odooskills_<feature>/
├── screenshots/             ← Captures d'écran par article
│   └── <slug>/
│       ├── 01-...png
│       └── 02-...png
├── templates/               ← Templates Markdown réutilisables
│   ├── technique.md
│   └── fonctionnel.md
├── assets/                  ← Logo, illustrations communes
├── CATEGORIES.md            ← Mapping catégorisé des 46 articles cibles
├── CONVENTIONS.md           ← Règles de rédaction, captures, code
└── README.md
```

## Workflow d'un article

```
1. Choisir un article cible dans CATEGORIES.md (statut TODO)
2. Si technique → développer le module dans modules/<slug>/
3. Tester le module en local
4. Prendre les captures sur la base "formation" du VPS
5. Rédiger l'article dans articles/<slug>.md à partir du template
6. Validation BENHAMIDA Mustapha
7. Publication dans Odoo Website (VPS)
8. Mise à jour du statut dans CATEGORIES.md
```

**Règle d'or** : on ne publie aucun article qui n'a pas été testé localement.

## Mission migration

Ce repo accompagne la migration du blog statique HTML actuel (88 URLs) vers une plateforme Odoo 19 Website moderne, avec :
- **46 articles cibles** consolidés (-48% de doublons multi-versions)
- **Redirections 301** pour préserver le SEO
- **Code source testé** pour chaque article technique
- **Captures réelles** depuis une base Odoo 19 dédiée

Voir aussi `blog-migration/` à la racine du projet (matrice de décision, scripts).

## Licence

Contenu rédactionnel : **CC-BY-4.0**
Code des modules : **LGPL-3** (compatible Odoo CE)

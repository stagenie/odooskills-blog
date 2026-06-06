# Conventions de rédaction — OdooSkills Blog

Document de référence pour garantir la cohérence entre tous les articles.

## 1. Langue et style

- **Langue** : français
- **Ton** : professionnel mais accessible, tutoiement de l'audience à éviter (préférer "vous" ou la forme impersonnelle)
- **Niveau** : on présume que le lecteur connaît les bases d'Odoo (interface admin, modules)
- **Longueur cible** : 1 500 à 3 000 mots par article (équivalent ~10 minutes de lecture)
- **Phrases courtes**, paragraphes de 3-5 lignes max
- **Pas d'emojis** dans le corps des articles

## 2. Slug d'URL

- Format : `mot-cle-principal-odoo-19` ou `action-objet-odoo-19`
- Tout en minuscules, séparé par des tirets
- Suffixe `-odoo-19` pour positionner sur la version
- Maximum 60 caractères
- Exemples :
  - ✅ `installer-odoo-19-windows`
  - ✅ `gestion-stock-entrepots-odoo-19`
  - ❌ `comment-installer-odoo-19-sur-windows-10-et-11-rapidement`

## 3. Structure obligatoire

Tout article doit comporter dans cet ordre :

1. **H1** : titre complet (60 caractères max)
2. **Métadonnées** (frontmatter ou paragraphe d'intro) : auteur, date, catégorie, durée de lecture
3. **Introduction** : 2-3 paragraphes posant le contexte et l'objectif
4. **Sommaire** (auto si Odoo Website le gère, sinon liste de liens d'ancres)
5. **Sections principales** en H2/H3
6. **Conclusion** + appel à l'action (commenter, lire un autre article lié)
7. **Articles liés** : 2 à 3 liens internes vers d'autres articles du blog

## 4. Code source

### Coloration syntaxique
Utiliser les blocs ``` avec le langage explicite :

````markdown
```python
class MyModel(models.Model):
    _name = "my.model"
    _description = "Mon modèle"

    name = fields.Char(required=True)
```

```xml
<record id="view_my_model_form" model="ir.ui.view">
    <field name="name">my.model.form</field>
    <field name="model">my.model</field>
    <field name="arch" type="xml">
        <form>
            <field name="name"/>
        </form>
    </field>
</record>
```

```bash
sudo apt update
sudo apt install postgresql
```
````

### Règle d'or : tout code doit être testé
- Articles techniques : le code provient **du module développé** dans `modules/<slug>/`
- Avant publication, le module doit être installé sans erreur sur une base Odoo 19 propre
- Référencer le code source GitHub à la fin de l'article

### Conventions de nommage Odoo 19
Voir aussi `CLAUDE.md` à la racine du projet pour les patterns Odoo 19 obligatoires :
- Plus de `attrs` ni `states` → utiliser `invisible="..."`, `readonly="..."`
- `view_mode` : `list,form` (jamais `tree`)
- `_unique_field = models.Constraint(...)` (plus de `_sql_constraints`)
- `t-out` au lieu de `t-esc`
- etc.

## 5. Captures d'écran

### Format technique
- **Résolution** : **1920 × 1080** (Full HD)
- **Cadrage** : zone applicative Odoo (pas de barre d'OS, pas de barre de tâches)
- **Format fichier** : PNG (qualité, pas de perte)
- **Optimisation** : passer chaque PNG dans `pngquant` ou `optipng` avant commit

### Annotations
- **Couleur** : rouge `#E63946` (cohérent avec l'identité)
- **Outils acceptés** : flèches, cercles, encadrés, numéros (1, 2, 3...)
- **Texte** : éviter le texte sur les captures, préférer la légende sous l'image
- **Ne pas masquer** d'éléments importants de l'interface

### Nommage
Format : `NN-action-courte.png`
- `NN` : numéro à 2 chiffres (01, 02, ...) pour respecter l'ordre de lecture
- Exemples :
  - `01-installation-postgresql.png`
  - `02-creer-base-donnees.png`
  - `03-formulaire-creation-utilisateur.png`

### Stockage
- Toutes les captures d'un article vont dans `screenshots/<slug>/`
- Référencées dans le Markdown : `![Description](../screenshots/<slug>/01-action.png)`

## 6. Modules de démonstration

### Quand en créer un
- Pour tout article **technique** qui contient du code Odoo (modèles, vues, ORM, héritage, controllers, etc.)
- Pas nécessaire pour les articles d'installation, configuration système, ou articles fonctionnels (manipulation backend)

### Convention de nommage
- Dossier dans `modules/<slug>/`
- Nom du module : `odooskills_<feature_courte>` (ex : `odooskills_first_app`, `odooskills_inheritance`)
- Préfixe `odooskills_` pour ne PAS confondre avec les modules ADICOPS (`adi_*`)

### Manifest minimum
```python
{
    "name": "OdooSkills - <Description>",
    "version": "19.0.1.0.0",
    "category": "Tutorial",
    "summary": "Module d'exemple pour l'article OdooSkills <slug>",
    "author": "BENHAMIDA Mustapha (OdooSkills)",
    "website": "https://odooskills.com",
    "license": "LGPL-3",
    "depends": ["base"],
    "data": [],
    "installable": True,
    "application": False,
}
```

### Test obligatoire
Avant publication de l'article, le module doit :
1. S'installer sans erreur : `./odoo-bin -c config/odoo.conf -i odooskills_<feature> -d <test_db> --stop-after-init`
2. Être upgradable : `./odoo-bin -c config/odoo.conf -u odooskills_<feature> -d <test_db> --stop-after-init`
3. Ne pas casser les modules dépendants

## 7. SEO

### Métadonnées Odoo Website
Renseigner systématiquement dans l'admin :
- **Titre SEO** : titre optimisé (60 caractères max)
- **Meta description** : 150-160 caractères, contient les mots-clés cibles
- **Slug URL** : conforme aux règles section 2
- **Image de couverture** : 1200×630 (Open Graph), nommée `<slug>-cover.png`

### Structure du contenu
- 1 seul `<h1>` par article (titre principal)
- Balises `<h2>` pour les sections principales (5 à 8 max)
- Mots-clés cibles dans : titre, intro, première H2, conclusion, alt des images
- Pas de bourrage de mots-clés (penser lecture humaine d'abord)

### Liens
- **Internes** : 2-3 liens vers d'autres articles du blog par article
- **Externes** : vers documentation officielle Odoo, OCA, Github (autorité)
- **Tous les liens externes** ouvrent dans un nouvel onglet (`target="_blank" rel="noopener"`)

## 8. Workflow Git

### Commits
Format : `<type>(<scope>): <description>`

Types :
- `article(slug)` : ajout/modification d'un article
- `module(slug)` : ajout/modification d'un module
- `screenshot(slug)` : ajout de captures
- `template` : modification de templates
- `docs` : documentation du repo
- `fix(slug)` : correction d'un article publié

Exemples :
```
article(installer-odoo-19-windows): rédaction initiale
module(developper-premiere-app): ajout fichier views.xml
screenshot(gestion-stock-odoo-19): ajout 12 captures step-by-step
fix(heritage-modeles-odoo-19): correction code XML invalide
```

### Branches
- `19.0` : production Odoo 19 (branche par défaut)
- `18.0` : versions Odoo 18 (legacy)
- Pas de branches feature pour les articles individuels (commit direct sur la branche version)

## 9. Validation avant publication

Checklist obligatoire avant de pousser un article en ligne sur le VPS :

- [ ] Article rédigé dans `articles/<slug>.md`
- [ ] Module de démo testé en local (si technique)
- [ ] Toutes les captures dans `screenshots/<slug>/`
- [ ] Slug et meta SEO conformes aux conventions
- [ ] Liens internes ajoutés (2-3 articles liés)
- [ ] Code dans l'article identique à celui du module testé
- [ ] Validation BENHAMIDA Mustapha
- [ ] Statut mis à jour dans `CATEGORIES.md`

## 10. Emplacement des nouveaux articles (règle post-migration 2026-06)

La migration du blog statique est **terminée**. Le dossier `blog-migration/` à la racine du
projet est désormais une **archive GELÉE (read-only)** — on n'y écrit plus.

Tout nouvel article OdooSkills (technique, fonctionnel ou autre) se place ici :

| Artefact | Emplacement |
|----------|-------------|
| Source article (HTML/MD) | `content/blog/articles/<slug>.html` |
| Cover PNG | `content/blog/assets/covers/` (fonctionnel → `covers-functional/`) |
| Module démo | `content/blog/modules/<slug>/` |
| Captures | `content/blog/screenshots/<slug>/` |
| Suivi éditorial | `content/blog/CATEGORIES.md` |

**Hors de ce submodule public** (racine du projet) :

| Artefact | Emplacement | Raison |
|----------|-------------|--------|
| Veille / research | `.specs/blog-research/` | notes internes |
| Briefs / plans | `.specs/plans/` ou `.specs/scratchpad/` | notes internes |
| Scripts de publication | `tools/blog/` | **contiennent des credentials DB** → jamais dans un repo public |

> ⚠️ `content/blog` est un submodule **public**. Aucun credential, aucune veille interne,
> aucun script-à-mot-de-passe ne doit y être committé.

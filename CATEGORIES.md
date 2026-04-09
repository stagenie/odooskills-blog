# Catégories & articles cibles — OdooSkills Blog

Mapping des **46 articles cibles** en 6 catégories, avec leur template recommandé et statut de production.

Généré depuis `blog-migration/decision_matrix.csv`. Régénérer avec :
```bash
cd blog-migration && python3 build_categories.py
```

## Légende statut

| Statut | Sens |
|--------|------|
| `TODO` | Pas commencé |
| `WIP` | En cours de rédaction / module en dev |
| `REVIEW` | En attente de validation BENHAMIDA Mustapha |
| `DONE` | Publié sur le VPS |

## Synthèse

- **Total articles cibles** : **48**
- **Catégories** : **6**
- **Articles techniques** (avec module) : **20**
- **Articles fonctionnels** : **28**

| # | Catégorie | Articles | Mots totaux |
|---|-----------|---------:|------------:|
| 01 | **Installation & Administration** | 7 | 17,594 |
| 02 | **Développement Odoo 19** | 13 | 31,795 |
| 03 | **Gestion (ERP)** | 13 | 27,299 |
| 04 | **Site Web & E-commerce** | 6 | 15,179 |
| 05 | **Marketing & Communication** | 3 | 8,637 |
| 06 | **Editorial & Découverte** | 6 | 9,247 |

## 01. Installation & Administration

`01-installation-administration` — **7 articles**

| Statut | Slug cible | Template | Sources | Mots | Priorité |
|--------|------------|----------|--------:|-----:|----------|
| TODO | `installer-odoo-19-ubuntu` | technique | 🔀6 | 6,722 | P1 |
| TODO | `installer-odoo-19-windows` | technique | 🔀4 | 2,207 | P1 |
| TODO | `configurer-environnement-developpement-odoo-19` | technique | 🔀3 | 3,398 | P1 |
| TODO | `installer-odoo-19-docker` | technique | 🔀2 | 2,714 | P2 |
| TODO | `gestion-bases-de-donnees-odoo-19` | technique |   1 | 888 | P3 |
| TODO | `sauvegardes-automatiques-odoo-19` | technique |   1 | 864 | P3 |
| TODO | `installer-modules-odoo-19` | technique |   1 | 801 | P3 |

<details>
<summary>Détail des sources fusionnées (4 articles)</summary>

### `configurer-environnement-developpement-odoo-19`

- `comment-configurer-pycharm-pour-le-developpement-odoo-13-sous-ubuntu20-0` (1251w, v13) — pycharm v13
- `environnement-developpement-odoo-p1` (798w, n/a) — env dev p1
- `environnement-developpement-odoo-p2` (1349w, v14) — env dev p2

### `installer-odoo-19-docker`

- `deployer-odoo-16-sur-docker-dans-ubuntu-22-04` (1036w, v16) — v16 docker p1
- `deployer-odoo-16-sur-docker-dans-ubuntu-22-04-p2` (1678w, v16) — v16 docker p2

### `installer-odoo-19-ubuntu`

- `comment-installer-odoo-13-sur-ubuntu18` (1206w, v13) — v13 ubuntu18
- `install-odoo14-sur-ubuntu20` (627w, v14) — v14 ubuntu20
- `installer-et-configurer-odoo-15-sur-ubuntu-20-04p1` (1378w, v15) — v15 ubuntu20 partie 1
- `installer-et-configurer-odoo-15-sur-ubuntu-20-04p2` (1246w, v15) — v15 ubuntu20 partie 2
- `installer-et-configurer-odoo15-p3` (1695w, v15) — v15 ubuntu20 partie 3
- `installer-et-confiigurer-odoo15-sur-ubntu20-04` (570w, v15) — v15 doublon (typo url)

### `installer-odoo-19-windows`

- `comment-installer-odoo-16-sur-winows-10-11` (729w, v16) — v16 windows
- `install-odoo14-windows10` (411w, v14) — v14 windows
- `installer-odoo-sur-windows` (414w, v13) — v13 windows
- `installer-odoo15-sur-windows16` (653w, v15) — v15 windows

</details>

## 02. Développement Odoo 19

`02-developpement-odoo-19` — **13 articles**

| Statut | Slug cible | Template | Sources | Mots | Priorité |
|--------|------------|----------|--------:|-----:|----------|
| TODO | `developper-premiere-application-odoo-19` | technique | 🔀3 | 6,335 | P1 |
| TODO | `manipulation-enregistrements-orm-odoo-19` | technique | 🔀3 | 5,561 | P1 |
| TODO | `heritage-modeles-odoo-19` | technique | 🔀3 | 5,192 | P1 |
| TODO | `premiere-approche-developpement-odoo-19` | technique | 🔀2 | 2,929 | P2 |
| TODO | `vues-de-base-odoo-19` | technique |   1 | 1,728 | P3 |
| TODO | `relations-entre-modeles-odoo-19` | technique |   1 | 1,508 | P3 |
| TODO | `champs-non-relationnels-odoo-19` | technique |   1 | 1,378 | P3 |
| TODO | `contraintes-champs-calcules-odoo-19` | technique |   1 | 1,367 | P3 |
| TODO | `cook-book-odoo-19` | technique |   1 | 1,301 | P3 |
| TODO | `modeles-de-base-odoo-19` | technique |   1 | 1,298 | P3 |
| TODO | `attributs-modeles-odoo-19` | technique |   1 | 1,131 | P3 |
| TODO | `architecture-technique-odoo-19` | technique |   1 | 1,118 | P3 |
| TODO | `hierarchie-modeles-odoo-19` | technique |   1 | 949 | P3 |

<details>
<summary>Détail des sources fusionnées (4 articles)</summary>

### `developper-premiere-application-odoo-19`

- `ceer-votre-application-odoo-14-partie1` (2276w, v14) — doublon v14 p1
- `ceer-votre-application-odoo-14-partie2` (1017w, v14) — doublon v14 p2
- `developpement-de-votre-premiere-application-en-utilisant-le-framework-odoo-13` (3042w, v13) — 

### `heritage-modeles-odoo-19`

- `comprendre-le-mecanisme-dheritage-sur-odoo` (2559w, n/a) — intro héritage
- `etendre-les-modeles-odoo-en-utilisant-le-mecanisme-heritage-p-01` (1368w, n/a) — héritage p1
- `etendre-les-modeles-odoo-en-utilisant-le-mecanisme-heritage-p-02` (1265w, n/a) — héritage p2

### `manipulation-enregistrements-orm-odoo-19`

- `manipulation-des-enregistrements-des-modeles-p1` (2229w, n/a) — ORM p1
- `manipulation-des-enregistrements-des-modeles-p2` (1565w, n/a) — ORM p2
- `manipulation-des-enregistrements-des-modeles-p3` (1767w, n/a) — ORM p3

### `premiere-approche-developpement-odoo-19`

- `premiere-approche-technique-2sur2` (1876w, n/a) — p2
- `votre-premiere-approche-technique1sur2` (1053w, n/a) — p1

</details>

## 03. Gestion (ERP)

`03-gestion-erp` — **13 articles**

| Statut | Slug cible | Template | Sources | Mots | Priorité |
|--------|------------|----------|--------:|-----:|----------|
| TODO | `gestion-achats-odoo-19` | fonctionnel | 🔀3 | 4,153 | P1 |
| TODO | `gestion-stock-entrepots-transferts-odoo-19` | fonctionnel | 🔀2 | 3,783 | P2 |
| TODO | `recrutement-en-ligne-odoo-19` | fonctionnel | 🔀2 | 2,496 | P2 |
| TODO | `gestion-ventes-odoo-19` | fonctionnel | 🔀2 | 2,335 | P2 |
| TODO | `gestion-crm-odoo-19` | fonctionnel |   1 | 1,889 | P3 |
| TODO | `gestion-rh-odoo-19` | fonctionnel |   1 | 1,862 | P3 |
| TODO | `gestion-stock-uom-conditionnement-odoo-19` | fonctionnel |   1 | 1,825 | P3 |
| TODO | `gestion-depenses-presences-odoo-19` | fonctionnel |   1 | 1,793 | P3 |
| TODO | `comptabilite-odoo-19` | fonctionnel |   1 | 1,751 | P3 |
| TODO | `gestion-conges-odoo-19` | fonctionnel |   1 | 1,720 | P3 |
| TODO | `gestion-production-mrp-odoo-19` | fonctionnel |   1 | 1,561 | P3 |
| TODO | `tracabilite-lots-numeros-serie-odoo-19` | fonctionnel |   1 | 1,379 | P3 |
| TODO | `gestion-routes-multi-etapes-odoo-19` | fonctionnel |   1 | 752 | P3 |

<details>
<summary>Détail des sources fusionnées (4 articles)</summary>

### `gestion-achats-odoo-19`

- `gestion-des-achats-avec-odoo16-2` (1798w, v16) — v16 p2
- `gestion-des-achats-avec-odoo16-p-01` (1183w, v16) — v16 p1
- `gestion-des-achats-sous-odoo-13` (1172w, v13) — v13

### `gestion-stock-entrepots-transferts-odoo-19`

- `gestion-de-stock-partie-01-gestion-des-entrepots-et-transferts-de-stock` (1743w, n/a) — 
- `gestion-de-stock-sous-odoo-13` (2040w, v13) — doublon v13

### `gestion-ventes-odoo-19`

- `gestion-commerciale-odoo-13` (802w, v13) — doublon v13
- `gestion-des-ventes-sous-doo-13` (1533w, n/a) — 

### `recrutement-en-ligne-odoo-19`

- `gestion-de-recrutement-en-ligne-et-en-backend-avec-odoo-p1` (1251w, n/a) — 
- `gestion-de-recrutement-en-ligne-et-en-backend-avec-odoo-p2` (1245w, n/a) — p2

</details>

## 04. Site Web & E-commerce

`04-site-web-ecommerce` — **6 articles**

| Statut | Slug cible | Template | Sources | Mots | Priorité |
|--------|------------|----------|--------:|-----:|----------|
| TODO | `creer-site-web-odoo-19` | fonctionnel | 🔀2 | 4,026 | P1 |
| TODO | `elearning-cours-en-ligne-odoo-19` | fonctionnel | 🔀2 | 3,182 | P2 |
| TODO | `gestion-ecommerce-odoo-19` | fonctionnel | 🔀2 | 2,692 | P2 |
| TODO | `site-web-dynamique-ssl-odoo-19` | fonctionnel | 🔀2 | 2,366 | P2 |
| TODO | `gestion-forums-odoo-19` | fonctionnel |   1 | 1,557 | P3 |
| TODO | `creer-blog-pro-odoo-19` | fonctionnel |   1 | 1,356 | P3 |

<details>
<summary>Détail des sources fusionnées (4 articles)</summary>

### `creer-site-web-odoo-19`

- `creer-rapidement-et-facilement-un-site-web-moderne-et-dynamqie-avec-odoo-16` (1595w, v16) — v16
- `creer-site-moderne-avec-cms-odoo` (2431w, v14) — cms

### `elearning-cours-en-ligne-odoo-19`

- `gerer-et-publier-des-cours-en-ligne-avec-la-plateforme-e-learning-dodoo-14-partie-1` (1617w, v14) — 
- `gerer-et-publier-des-cours-en-ligne-avec-la-plateforme-e-learning-dodoo-14-partie-2` (1565w, v14) — p2

### `gestion-ecommerce-odoo-19`

- `gestion-e-commerce-avec-odoo-partie1` (1295w, v14) — 
- `gestion-e-commerce-avec-odoo-partie2` (1397w, v14) — p2

### `site-web-dynamique-ssl-odoo-19`

- `creation-dun-site-web-dynamique-avec-certificat-ssl-en-utilisant-odoo-partie-01` (1364w, v16) — ssl p1
- `creation-dun-site-web-dynamique-avec-certificat-ssl-en-utilisant-odoo-partie-02` (1002w, v16) — ssl p2

</details>

## 05. Marketing & Communication

`05-marketing-communication` — **3 articles**

| Statut | Slug cible | Template | Sources | Mots | Priorité |
|--------|------------|----------|--------:|-----:|----------|
| TODO | `gestion-evenements-odoo-19` | fonctionnel | 🔀3 | 4,641 | P1 |
| TODO | `gestion-sondages-odoo-19` | fonctionnel |   1 | 2,076 | P3 |
| TODO | `email-marketing-odoo-19` | fonctionnel |   1 | 1,920 | P3 |

<details>
<summary>Détail des sources fusionnées (1 articles)</summary>

### `gestion-evenements-odoo-19`

- `gestion-des-evenements-avec-odoo-p1` (1819w, n/a) — 
- `gestion-des-evenements-avec-odoo-p2` (1224w, n/a) — p2
- `gestion-des-evenements-avec-odoo-p3` (1598w, n/a) — p3

</details>

## 06. Editorial & Découverte

`06-editorial-decouverte` — **6 articles**

| Statut | Slug cible | Template | Sources | Mots | Priorité |
|--------|------------|----------|--------:|-----:|----------|
| TODO | `decouverte-odoo-19` | fonctionnel | 🔀3 | 4,089 | P1 |
| TODO | `livres-odoo-consultant-2026` | fonctionnel |   1 | 1,764 | P3 |
| TODO | `nouveautes-odoo-19` | fonctionnel |   1 | 1,334 | P3 |
| TODO | `odoo-enterprise-vs-community` | fonctionnel |   1 | 1,096 | P3 |
| TODO | `odoo-pour-les-entreprises-pourquoi` | fonctionnel |   1 | 483 | P3 |
| TODO | `avantages-odoo-developpeurs` | fonctionnel |   1 | 481 | P3 |

<details>
<summary>Détail des sources fusionnées (1 articles)</summary>

### `decouverte-odoo-19`

- `a-la-decouverte-odoo-13` (1243w, v13) — fusion avec interface-odoo-13 et nouveautes-odoo14
- `decouvrir-odoo14-interface` (1673w, v14) — interface v14
- `interface-odoo-13` (1173w, v13) — interface

</details>

## Priorités de production

- **P1** (haute) : articles avec ≥ 3 sources fusionnées OU ≥ 4 000 mots → fort potentiel SEO/contenu, à attaquer en premier
- **P2** (moyenne) : articles avec 2 sources fusionnées
- **P3** (basse) : articles uniques, contenu déjà cohérent

## Notes

- Les articles **techniques** nécessitent un module testé dans `modules/<slug>/`
- Les articles **fonctionnels** s'appuient sur des captures de la base "formation" du VPS
- Pour rééditer ce fichier après changement de matrice : `cd blog-migration && python3 build_categories.py`
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

- **Total articles cibles** : **46**
- **Catégories** : **6**
- **Articles techniques** (avec module) : **20**
- **Articles fonctionnels** : **26**

| # | Catégorie | Articles | Mots totaux |
|---|-----------|---------:|------------:|
| 01 | **Installation & Administration** | 7 | 22,018 |
| 02 | **Développement Odoo 19** | 13 | 39,298 |
| 03 | **Gestion (ERP)** | 12 | 30,385 |
| 04 | **Site Web & E-commerce** | 6 | 19,420 |
| 05 | **Marketing & Communication** | 3 | 11,221 |
| 06 | **Editorial & Découverte** | 5 | 9,528 |

## 01. Installation & Administration

`01-installation-administration` — **7 articles**

| Statut | Slug cible | Template | Sources | Mots | Priorité |
|--------|------------|----------|--------:|-----:|----------|
| TODO | `installer-odoo-19-ubuntu` | technique | 🔀6 | 7,767 | P1 |
| TODO | `installer-odoo-19-windows` | technique | 🔀4 | 3,164 | P1 |
| TODO | `configurer-environnement-developpement-odoo-19` | technique | 🔀3 | 4,575 | P1 |
| TODO | `installer-odoo-19-docker` | technique | 🔀2 | 3,021 | P2 |
| TODO | `gestion-bases-de-donnees-odoo-19` | technique |   1 | 1,307 | P3 |
| TODO | `installer-modules-odoo-19` | technique |   1 | 1,216 | P3 |
| TODO | `sauvegardes-automatiques-odoo-19` | technique |   1 | 968 | P3 |

<details>
<summary>Détail des sources fusionnées (4 articles)</summary>

### `configurer-environnement-developpement-odoo-19`

- `comment-configurer-pycharm-pour-le-developpement-odoo-13-sous-ubuntu20-0` (1495w, v13) — pycharm v13
- `environnement-developpement-odoo-p1` (1191w, v14) — env dev p1
- `environnement-developpement-odoo-p2` (1889w, v14) — env dev p2

### `installer-odoo-19-docker`

- `deployer-odoo-16-sur-docker-dans-ubuntu-22-04` (1178w, v16) — v16 docker p1
- `deployer-odoo-16-sur-docker-dans-ubuntu-22-04-p2` (1843w, v16) — v16 docker p2

### `installer-odoo-19-ubuntu`

- `comment-installer-odoo-13-sur-ubuntu18` (1412w, v13) — v13 ubuntu18
- `install-odoo14-sur-ubuntu20` (1023w, v14) — v14 ubuntu20
- `installer-et-configurer-odoo-15-sur-ubuntu-20-04p1` (1486w, v15) — v15 ubuntu20 partie 1
- `installer-et-configurer-odoo-15-sur-ubuntu-20-04p2` (1345w, v15) — v15 ubuntu20 partie 2
- `installer-et-configurer-odoo15-p3` (1824w, v15) — v15 ubuntu20 partie 3
- `installer-et-confiigurer-odoo15-sur-ubntu20-04` (677w, v15) — v15 doublon (typo url)

### `installer-odoo-19-windows`

- `comment-installer-odoo-16-sur-winows-10-11` (837w, v16) — v16 windows
- `install-odoo14-windows10` (889w, v14) — v14 windows
- `installer-odoo-sur-windows` (623w, v13) — v13 windows
- `installer-odoo15-sur-windows16` (815w, v15) — v15 windows

</details>

## 02. Développement Odoo 19

`02-developpement-odoo-19` — **13 articles**

| Statut | Slug cible | Template | Sources | Mots | Priorité |
|--------|------------|----------|--------:|-----:|----------|
| TODO | `developper-premiere-application-odoo-19` | technique | 🔀3 | 7,606 | P1 |
| TODO | `manipulation-enregistrements-orm-odoo-19` | technique | 🔀3 | 6,771 | P1 |
| TODO | `heritage-modeles-odoo-19` | technique | 🔀3 | 6,308 | P1 |
| TODO | `premiere-approche-developpement-odoo-19` | technique | 🔀2 | 3,408 | P2 |
| TODO | `vues-de-base-odoo-19` | technique |   1 | 1,981 | P3 |
| TODO | `relations-entre-modeles-odoo-19` | technique |   1 | 1,919 | P3 |
| TODO | `champs-non-relationnels-odoo-19` | technique |   1 | 1,817 | P3 |
| TODO | `contraintes-champs-calcules-odoo-19` | technique |   1 | 1,777 | P3 |
| TODO | `modeles-de-base-odoo-19` | technique |   1 | 1,717 | P3 |
| TODO | `cook-book-odoo-19` | technique |   1 | 1,676 | P3 |
| TODO | `attributs-modeles-odoo-19` | technique |   1 | 1,586 | P3 |
| TODO | `hierarchie-modeles-odoo-19` | technique |   1 | 1,404 | P3 |
| TODO | `architecture-technique-odoo-19` | technique |   1 | 1,328 | P3 |

<details>
<summary>Détail des sources fusionnées (4 articles)</summary>

### `developper-premiere-application-odoo-19`

- `ceer-votre-application-odoo-14-partie1` (2825w, v14) — doublon v14 p1
- `ceer-votre-application-odoo-14-partie2` (1445w, v14) — doublon v14 p2
- `developpement-de-votre-premiere-application-en-utilisant-le-framework-odoo-13` (3336w, v13) — 

### `heritage-modeles-odoo-19`

- `comprendre-le-mecanisme-dheritage-sur-odoo` (2865w, v13) — intro héritage
- `etendre-les-modeles-odoo-en-utilisant-le-mecanisme-heritage-p-01` (1770w, v14) — héritage p1
- `etendre-les-modeles-odoo-en-utilisant-le-mecanisme-heritage-p-02` (1673w, v14) — héritage p2

### `manipulation-enregistrements-orm-odoo-19`

- `manipulation-des-enregistrements-des-modeles-p1` (2661w, v14) — ORM p1
- `manipulation-des-enregistrements-des-modeles-p2` (1957w, v14) — ORM p2
- `manipulation-des-enregistrements-des-modeles-p3` (2153w, v14) — ORM p3

### `premiere-approche-developpement-odoo-19`

- `premiere-approche-technique-2sur2` (2117w, v13) — p2
- `votre-premiere-approche-technique1sur2` (1291w, v13) — p1

</details>

## 03. Gestion (ERP)

`03-gestion-erp` — **12 articles**

| Statut | Slug cible | Template | Sources | Mots | Priorité |
|--------|------------|----------|--------:|-----:|----------|
| TODO | `gestion-achats-odoo-19` | fonctionnel | 🔀3 | 4,684 | P1 |
| TODO | `gestion-stock-entrepots-transferts-odoo-19` | fonctionnel | 🔀2 | 4,198 | P1 |
| TODO | `recrutement-en-ligne-odoo-19` | fonctionnel | 🔀2 | 3,509 | P2 |
| TODO | `gestion-ventes-odoo-19` | fonctionnel | 🔀2 | 2,768 | P2 |
| TODO | `gestion-rh-odoo-19` | fonctionnel |   1 | 2,368 | P3 |
| TODO | `gestion-depenses-presences-odoo-19` | fonctionnel |   1 | 2,293 | P3 |
| TODO | `gestion-conges-odoo-19` | fonctionnel |   1 | 2,210 | P3 |
| TODO | `gestion-stock-uom-conditionnement-odoo-19` | fonctionnel |   1 | 2,042 | P3 |
| TODO | `comptabilite-odoo-19` | fonctionnel |   1 | 2,000 | P3 |
| TODO | `gestion-production-mrp-odoo-19` | fonctionnel |   1 | 1,784 | P3 |
| TODO | `tracabilite-lots-numeros-serie-odoo-19` | fonctionnel |   1 | 1,587 | P3 |
| TODO | `gestion-routes-multi-etapes-odoo-19` | fonctionnel |   1 | 942 | P3 |

<details>
<summary>Détail des sources fusionnées (4 articles)</summary>

### `gestion-achats-odoo-19`

- `gestion-des-achats-avec-odoo16-2` (1949w, v16) — v16 p2
- `gestion-des-achats-avec-odoo16-p-01` (1341w, v16) — v16 p1
- `gestion-des-achats-sous-odoo-13` (1394w, v13) — v13

### `gestion-stock-entrepots-transferts-odoo-19`

- `gestion-de-stock-partie-01-gestion-des-entrepots-et-transferts-de-stock` (1945w, v15) — 
- `gestion-de-stock-sous-odoo-13` (2253w, v13) — doublon v13

### `gestion-ventes-odoo-19`

- `gestion-commerciale-odoo-13` (1013w, v13) — doublon v13
- `gestion-des-ventes-sous-doo-13` (1755w, v13) — 

### `recrutement-en-ligne-odoo-19`

- `gestion-de-recrutement-en-ligne-et-en-backend-avec-odoo-p1` (1738w, v14) — 
- `gestion-de-recrutement-en-ligne-et-en-backend-avec-odoo-p2` (1771w, v14) — p2

</details>

## 04. Site Web & E-commerce

`04-site-web-ecommerce` — **6 articles**

| Statut | Slug cible | Template | Sources | Mots | Priorité |
|--------|------------|----------|--------:|-----:|----------|
| TODO | `creer-site-web-odoo-19` | fonctionnel | 🔀2 | 4,820 | P1 |
| TODO | `elearning-cours-en-ligne-odoo-19` | fonctionnel | 🔀2 | 4,233 | P1 |
| TODO | `gestion-ecommerce-odoo-19` | fonctionnel | 🔀2 | 3,769 | P2 |
| TODO | `site-web-dynamique-ssl-odoo-19` | fonctionnel | 🔀2 | 2,693 | P2 |
| TODO | `gestion-forums-odoo-19` | fonctionnel |   1 | 2,047 | P3 |
| TODO | `creer-blog-pro-odoo-19` | fonctionnel |   1 | 1,858 | P3 |

<details>
<summary>Détail des sources fusionnées (4 articles)</summary>

### `creer-site-web-odoo-19`

- `creer-rapidement-et-facilement-un-site-web-moderne-et-dynamqie-avec-odoo-16` (1757w, v16) — v16
- `creer-site-moderne-avec-cms-odoo` (3063w, v14) — cms

### `elearning-cours-en-ligne-odoo-19`

- `gerer-et-publier-des-cours-en-ligne-avec-la-plateforme-e-learning-dodoo-14-partie-1` (2125w, v14) — 
- `gerer-et-publier-des-cours-en-ligne-avec-la-plateforme-e-learning-dodoo-14-partie-2` (2108w, v14) — p2

### `gestion-ecommerce-odoo-19`

- `gestion-e-commerce-avec-odoo-partie1` (1824w, v14) — 
- `gestion-e-commerce-avec-odoo-partie2` (1945w, v14) — p2

### `site-web-dynamique-ssl-odoo-19`

- `creation-dun-site-web-dynamique-avec-certificat-ssl-en-utilisant-odoo-partie-01` (1538w, v16) — ssl p1
- `creation-dun-site-web-dynamique-avec-certificat-ssl-en-utilisant-odoo-partie-02` (1155w, v16) — ssl p2

</details>

## 05. Marketing & Communication

`05-marketing-communication` — **3 articles**

| Statut | Slug cible | Template | Sources | Mots | Priorité |
|--------|------------|----------|--------:|-----:|----------|
| TODO | `gestion-evenements-odoo-19` | fonctionnel | 🔀3 | 6,227 | P1 |
| TODO | `gestion-sondages-odoo-19` | fonctionnel |   1 | 2,569 | P3 |
| TODO | `email-marketing-odoo-19` | fonctionnel |   1 | 2,425 | P3 |

<details>
<summary>Détail des sources fusionnées (1 articles)</summary>

### `gestion-evenements-odoo-19`

- `gestion-des-evenements-avec-odoo-p1` (2320w, v14) — 
- `gestion-des-evenements-avec-odoo-p2` (1745w, v14) — p2
- `gestion-des-evenements-avec-odoo-p3` (2162w, v14) — p3

</details>

## 06. Editorial & Découverte

`06-editorial-decouverte` — **5 articles**

| Statut | Slug cible | Template | Sources | Mots | Priorité |
|--------|------------|----------|--------:|-----:|----------|
| TODO | `decouverte-odoo-19` | fonctionnel | 🔀3 | 4,922 | P1 |
| TODO | `nouveautes-odoo-19` | fonctionnel |   1 | 2,412 | P3 |
| TODO | `odoo-enterprise-vs-community` | fonctionnel |   1 | 1,144 | P3 |
| TODO | `avantages-odoo-developpeurs` | fonctionnel |   1 | 527 | P3 |
| TODO | `odoo-pour-les-entreprises-pourquoi` | fonctionnel |   1 | 523 | P3 |

<details>
<summary>Détail des sources fusionnées (1 articles)</summary>

### `decouverte-odoo-19`

- `a-la-decouverte-odoo-13` (1283w, v13) — fusion avec interface-odoo-13 et nouveautes-odoo14
- `decouvrir-odoo14-interface` (2259w, v14) — interface v14
- `interface-odoo-13` (1380w, v13) — interface

</details>

## Priorités de production

- **P1** (haute) : articles avec ≥ 3 sources fusionnées OU ≥ 4 000 mots → fort potentiel SEO/contenu, à attaquer en premier
- **P2** (moyenne) : articles avec 2 sources fusionnées
- **P3** (basse) : articles uniques, contenu déjà cohérent

## Notes

- Les articles **techniques** nécessitent un module testé dans `modules/<slug>/`
- Les articles **fonctionnels** s'appuient sur des captures de la base "formation" du VPS
- Pour rééditer ce fichier après changement de matrice : `cd blog-migration && python3 build_categories.py`
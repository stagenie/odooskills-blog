---
slug: <slug-de-l-article>
title: <Titre H1 — 60 caractères max>
seo_title: <Titre SEO si différent — 60 caractères max>
meta_description: <150-160 caractères, contenant les mots-clés cibles>
category: developpement-odoo-19
tags: [odoo-19, python, tutoriel]
author: BENHAMIDA Mustapha
date: YYYY-MM-DD
reading_time: <X minutes>
cover_image: ../screenshots/<slug>/cover.png
demo_module: ../modules/<slug>/odooskills_<feature>/
---

# <Titre principal de l'article>

> **À qui s'adresse cet article ?** <Décrire brièvement le profil cible (développeur débutant, intégrateur, etc.) et le niveau requis.>

> **Ce que vous allez apprendre :**
> - Point 1
> - Point 2
> - Point 3

## Sommaire

1. [Introduction](#introduction)
2. [Prérequis](#prerequis)
3. [Concepts clés](#concepts-cles)
4. [Mise en pratique](#mise-en-pratique)
5. [Test et validation](#test-et-validation)
6. [Pour aller plus loin](#pour-aller-plus-loin)
7. [Code source](#code-source)

## Introduction

<Posez le problème : pourquoi ce sujet est important, dans quel contexte on l'utilise. 2-3 paragraphes max.>

## Prérequis

Avant de commencer, vous devez disposer de :

- **Odoo 19** installé en local (Community ou Enterprise)
- **Python 3.10+**
- Connaissances de base d'Odoo (interface admin, création de modules)
- <Autre prérequis spécifique>

> **Astuce** : si vous n'avez pas encore installé Odoo 19, consultez notre guide [Installer Odoo 19 sur Ubuntu](installer-odoo-19-ubuntu) ou [Installer Odoo 19 sur Windows](installer-odoo-19-windows).

## Concepts clés

<Expliquez les concepts théoriques nécessaires avant de plonger dans le code. Utilisez des schémas si pertinent.>

### Concept 1

<Description et exemple>

### Concept 2

<Description et exemple>

## Mise en pratique

### Étape 1 — <Action>

<Explication de ce qu'on va faire et pourquoi.>

```python
# Fichier : models/my_model.py
from odoo import models, fields

class MyModel(models.Model):
    _name = "odooskills.example"
    _description = "Exemple OdooSkills"

    name = fields.Char(string="Nom", required=True)
    active = fields.Boolean(default=True)
```

![Capture explicative](../screenshots/<slug>/01-action.png)
*Légende de la capture*

### Étape 2 — <Action>

<Explication>

```xml
<!-- Fichier : views/my_model_views.xml -->
<odoo>
    <record id="view_my_model_form" model="ir.ui.view">
        <field name="name">odooskills.example.form</field>
        <field name="model">odooskills.example</field>
        <field name="arch" type="xml">
            <form>
                <sheet>
                    <field name="name"/>
                </sheet>
            </form>
        </field>
    </record>
</odoo>
```

![Capture explicative](../screenshots/<slug>/02-action.png)
*Légende de la capture*

### Étape 3 — <Action>

<...>

## Test et validation

Une fois le module créé, on l'installe et on vérifie qu'il fonctionne :

```bash
# Installation depuis la ligne de commande
./odoo-bin -c config/odoo.conf -d ma_base -i odooskills_example --stop-after-init

# Ou depuis l'interface : Apps → Update Apps List → chercher "OdooSkills"
```

![Module installé](../screenshots/<slug>/03-installation.png)

**Vérifications à faire :**
- [ ] Le module apparaît dans la liste des Apps
- [ ] L'installation se termine sans erreur
- [ ] La nouvelle vue est accessible depuis le menu
- [ ] Les contraintes fonctionnent (tester un cas d'erreur)

## Pour aller plus loin

<Suggestions d'extension : sujets connexes, articles avancés, ressources externes.>

- [Documentation officielle Odoo](https://www.odoo.com/documentation/19.0/) — sur le sujet
- [Article OdooSkills lié 1](slug-article-lie-1)
- [Article OdooSkills lié 2](slug-article-lie-2)

## Code source

Le code complet de ce tutoriel est disponible sur GitHub :

🔗 **[odooskills-blog/modules/<slug>/](https://github.com/stagenie/odooskills-blog/tree/19.0/modules/<slug>)**

```bash
git clone -b 19.0 https://github.com/stagenie/odooskills-blog.git
cd odooskills-blog/modules/<slug>
```

## Conclusion

<Récapitulez ce qu'on a appris en 3-4 phrases. Encouragez à passer à l'étape suivante.>

---

**Vous avez aimé cet article ?** Partagez-le et abonnez-vous à la newsletter OdooSkills pour ne manquer aucun nouveau tutoriel.

**Une question ?** Laissez un commentaire ci-dessous ou contactez-nous : info@odooskills.com

---

*Article rédigé par **BENHAMIDA Mustapha**, consultant technico-fonctionnel Odoo et fondateur d'**ADICOPS**.*

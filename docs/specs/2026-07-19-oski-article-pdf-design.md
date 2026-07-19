# oski_article_pdf — L'article en PDF contre un email

**Date** : 2026-07-19
**Statut** : design validé, prêt pour plan d'implémentation
**Contexte amont** : abandon de la remise-à-l'inscription (voir mémoire `oski-lead-magnet-checkpoint`, section REVERT 19/07)

---

## 1. Objectif

Offrir à chaque lecteur du blog OdooSkills un **guide PDF soigné** de l'article qu'il lit — ou de la **série entière** si l'article en fait partie — en échange de son email. Sans interruption de lecture : pas de popup, pas de modal imposée. Le lecteur qui ne veut rien donner continue de lire normalement.

À terme, chaque nouvel article publié dispose de son PDF, généré automatiquement.

### Ce qui a motivé ce choix

La capture par popup avec remise a échoué (mesure du 19/07 : 1 seule offre créée en 6 jours, et c'était un test interne ; inscriptions passées de 2,13/j à 0,77/j). Le PDF renverse la logique : la contrepartie est un contenu utile, demandé par un lecteur déjà engagé, au lieu d'une remise poussée à un visiteur qui n'a rien demandé.

---

## 2. Décisions actées

| Sujet | Décision | Raison |
|---|---|---|
| Moteur PDF | **WeasyPrint** | Voir §3 — arbitré sur rendu d'essai réel |
| Templating | **QWeb** (`_render_qweb_html`) puis WeasyPrint | Garde les gabarits Odoo, ne change que le backend de rendu |
| Module | Nouveau **`oski_article_pdf`**, dépend de `oski_lead_magnet` | Génération et capture = deux responsabilités |
| Génération | **Automatisée, déclenchée à la publication** (via `ir.cron._trigger()`) + action groupée | Le fait-main n'a jamais démarré depuis le 12/07 et ne survivrait pas à « un PDF par article » |
| Livraison | **Téléchargement immédiat + copie par email** | SPF/DKIM non confirmés : le téléchargement tient la promesse même si le mail échoue |
| Vocabulaire | « guide PDF », **jamais « ebook »** | Ne pas brouiller la frontière avec la ligne payante (24–50 €) |
| Popup | **Retiré** | Décision utilisateur du 19/07 |
| Moteur de coupons | **Conservé, dormant** (`offer_enabled=False`) | Servira aux campagnes promo par email |

---

## 3. Choix du moteur — arbitré sur rendu d'essai

Test réalisé le 19/07 sur l'article **116** (« Linux pour le dev Odoo », 206 blocs `<pre>/<code>`, 33 Ko), même HTML et même CSS passés dans trois moteurs.

**Découverte majeure** : le contenu des articles porte **déjà son propre style inline** — blocs de code sombres avec badge de langage, coloration syntaxique, encadrés « Nouveauté v19 » / « Définition », légendes de figures. Le PDF hérite du design éditorial du site ; le gabarit ne fournit que la charpente (couverture, marges, pieds de page, sauts).

| Moteur | Pages | Verdict |
|---|---|---|
| **WeasyPrint** | 13 | ✅ Retenu. Couverture pleine page, pied de page supprimé sur la couverture, texte justifié, images distantes récupérées, aucun artefact |
| Chrome headless | 14 | Meilleure coloration syntaxique, mais **peint les barres de défilement** (`overflow-x:auto`) dans le PDF |
| wkhtmltopdf 0.12.5 | 10 | **Ignore `@page :first`** → marge blanche et numéro de page sur la couverture |

WeasyPrint ignore `word-break: break-word` et `overflow-x` (avertissements au rendu) — et c'est précisément ce qui lui évite l'artefact de Chrome.

**Conséquence d'architecture** : WeasyPrint contourne le moteur PDF natif d'Odoo (`ir.actions.report` → wkhtmltopdf). On conserve QWeb pour le gabarit et on passe le HTML rendu à WeasyPrint.

---

## 4. Prérequis infrastructure

WeasyPrint dépend de Pango/Cairo au niveau système. **Vérifié sur le VPS prod (Ubuntu 24.04.4, Python 3.12.3) : absents.**

```
libpango-1.0    ABSENT
libpangoft2-1.0 ABSENT
libcairo2       ABSENT
libgdk-pixbuf   ABSENT
```

Étapes requises, à valider explicitement avant exécution :

1. `apt install libpango-1.0-0 libpangoft2-1.0-0 libcairo2 libgdk-pixbuf-2.0-0`
2. `pip install weasyprint==68.1` dans `/opt/odoo19/odoo-venv`

Version épinglée à **68.1**, celle du rendu d'essai (poste de dev, Python 3.12.3 — identique à la prod). Dépendances Python tirées automatiquement : `cffi`, `cssselect2`, `fonttools`, `Pillow`, `pydyf`, `Pyphen`, `tinycss2`, `tinyhtml5`.

Ubuntu 24.04 fournit Pango 1.52, compatible WeasyPrint 68.

**Repli si l'installation système est refusée** : générer les PDF hors ligne (poste de dev, où WeasyPrint est déjà présent) et téléverser les `ir.attachment` en prod par script. Le cron de génération continue devient alors manuel — c'est le seul point perdu.

---

## 5. Modèle de données

Les champs existants dans `oski_lead_magnet` sont conservés et remplis par le nouveau module (pas de transfert de propriété d'`ir.model.data`).

**`blog.post`** (champs existants) : `oski_pdf_attachment_id`, `oski_pdf_series_id`.

**`blog.post`** (ajouts) :
- `oski_series_seq` (Integer, défaut 10) — ordre éditorial dans la série. La date de publication ne reflète pas toujours l'ordre de lecture (T1…T6).
- `oski_pdf_generated_on` (Datetime) — date de génération.
- `oski_pdf_stale` (Boolean, calculé) — vrai si `write_date > oski_pdf_generated_on`, c.-à-d. article réécrit depuis la génération.

**`oski.pdf.series`** (ajouts) :
- `post_ids` (One2many inverse de `oski_pdf_series_id`)
- `subtitle` (Char)
- `generated_on` (Datetime)

---

## 6. Gabarit QWeb

Un gabarit unique sert l'article seul et la série ; la série est un **rendu QWeb unique sur tous les articles ordonnés**, pas une concaténation de PDF — pagination continue et sommaire cohérent.

Structure : couverture pleine page (fond `#714B67`, titre, sous-titre, méta, marque) → sommaire (séries uniquement) → contenu.

### Contraintes CSS établies par le rendu d'essai

- **Fond perdu de couverture** : `@page :first { margin: 0 }` + bloc `height: 297mm`.
- **Pied de page** : `@page { @bottom-center { content: "OdooSkills — " counter(page) } }`, neutralisé sur `:first`.
- **Blocs de code** : `white-space: pre-wrap` + `overflow-wrap: break-word` obligatoires. `word-break: break-word` est refusé par WeasyPrint (valeur invalide) — utiliser `overflow-wrap`.
- **Sauts** : `page-break-inside: avoid` sur `pre`, `table`, `tr`, `.alert`, `.card`, figures. `page-break-after: avoid` sur les titres.
- **⚠️ Défaut connu à corriger** : `page-break-inside: avoid` appliqué à un bloc de code très haut laisse jusqu'à un tiers de page blanc. Le gabarit doit **autoriser la coupure au-delà d'une hauteur seuil** (bloc plus haut que ~40 % de la page utile).
- `orphans: 3; widows: 3`.
- Images `/web/image/NNNN` **réécrites en URL absolue** avant rendu (WeasyPrint n'a pas de contexte de session).
- Sous-ensemble CSS couvrant les classes Bootstrap réellement présentes dans le contenu (tables, `alert`, `card`, `text-muted`, `blockquote`) — Bootstrap n'est pas chargé hors du site.

---

## 7. Génération

- `blog.post._oski_generate_pdf()` et `oski.pdf.series._oski_generate_pdf()` — rendent, produisent l'`ir.attachment` (non public, `access_token`), renseignent les champs de suivi.
- **Déclenchement à la publication.** `blog.post.write()` détecte le passage à `is_published=True` (ou la republication d'un article périmé) et appelle **`ir.cron._trigger()`** sur le cron de génération.

  `_trigger()` (vérifié présent en Odoo 19, `ir_cron.py:666`) planifie l'exécution au prochain réveil du worker cron, indépendamment de `nextcall`. Le rendu WeasyPrint se fait donc **hors requête HTTP** : la publication reste instantanée pour le rédacteur, et le PDF est disponible dans les secondes qui suivent. C'est le compromis entre « générer à la publication » et « ne pas bloquer la mise en ligne pendant plusieurs secondes de rendu ».

  Si l'article appartient à une série, c'est le PDF de la **série entière** qui est régénéré — publier T4 met à jour le guide contenant T1…T6.

- **Action groupée** sur la liste des articles : « Générer le guide PDF ». Sert la première vague de rattrapage sur les 121 articles existants, triée par `visits` décroissant (champ natif — pas besoin de GA4).
- **Filet de sécurité** : le même cron, en passe périodique, reprend ce qui est marqué `oski_pdf_stale` ou dépourvu de PDF — couvre les échecs de rendu et les articles modifiés sans repasser par une publication.
- Un article appartenant à une série résout le PDF de la série (`_oski_pdf_attachment` existant, inchangé).

Volumétrie : 121 articles publiés × ~0,5 Mo ≈ 60–150 Mo de filestore.

---

## 8. Livraison

Sur capture réussie (`_oski_capture_lead`, logique de dédup existante inchangée) :

1. URL tokenisée retournée au navigateur → **téléchargement immédiat** (comportement actuel).
2. **Nouveau** : email transactionnel contenant le lien, `force_send=True`.

Un inscrit existant n'est pas enregistré deux fois (upsert `res.partner` + `mailing.contact` déjà en place) et reçoit quand même son PDF.

Le libellé du bouton s'adapte : « Obtenir les N articles de la série en PDF » si série, « Obtenir cet article en PDF » sinon.

**Consentement** : la case marketing reste **séparée** de la livraison du PDF. La livraison est transactionnelle (le lecteur l'a demandée) ; l'inscription aux offres est un opt-in distinct. Son libellé doit continuer à mentionner les offres, puisque les remises futures partiront par email.

---

## 9. Retrait du popup

Désactivation des vues `oski_lead_magnet.lead_popup` et `lead_popup_inject`, retrait de l'initialisation popup dans `lead_popup.js`. Le **gate PDF reste actif** (`pdf_gate_*`). `offer_enabled` reste `False`.

---

## 10. Tests

- Rendu non vide sur un article riche (code, images, tables) ; nombre de pages > 1.
- Série : tous les articles présents, dans l'ordre `oski_series_seq`.
- Péremption : réécriture d'un article ⇒ `oski_pdf_stale` vrai ⇒ repris par le cron.
- Tri par `visits` de l'action groupée.
- Email de livraison envoyé, lien tokenisé, pièce jointe non publique.
- Non-régression : l'URL non tokenisée n'apparaît jamais dans le DOM.
- Non-régression : capture d'un email déjà inscrit ⇒ pas de doublon `mailing.contact`, PDF quand même livré.

---

## 11. Hors périmètre

- Coloration syntaxique côté PDF (déjà portée par le HTML des articles).
- Passe de polish manuel sur les articles les plus lus — possible plus tard, non requise.
- Campagnes promo par email sur la liste Prospects — sujet distinct.
- Portage du dispositif au blog AISkillsPro.

---

## 12. Risques

| Risque | Traitement |
|---|---|
| `apt install` sur le VPS de prod | Étape explicite, paquets standards Ubuntu, `apt remove` en repli |
| SPF/DKIM `odooers@` non confirmés | Le téléchargement immédiat tient la promesse sans dépendre du mail |
| Blancs de page sur gros blocs de code | Seuil de hauteur dans le gabarit (§6) — à valider visuellement sur 3 articles |
| Croissance du filestore | ~150 Mo maximum, surveillé |
| Articles au HTML atypique | Le cron isole les échecs par article et journalise, sans interrompre la vague |

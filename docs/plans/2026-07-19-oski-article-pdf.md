# oski_article_pdf — Plan d'implémentation

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Générer automatiquement un guide PDF soigné par article (ou par série) du blog OdooSkills, déclenché à la publication, et le livrer contre un email — téléchargement immédiat plus copie par email.

**Architecture:** Nouveau module `oski_article_pdf` dépendant de `oski_lead_magnet`. Le gabarit reste du QWeb ; le HTML rendu est passé à **WeasyPrint** au lieu du wkhtmltopdf natif d'Odoo. La publication d'un article appelle `ir.cron._trigger()`, ce qui exécute le rendu hors requête HTTP. Le PDF produit alimente les champs `oski_pdf_attachment_id` / `oski_pdf_series_id` déjà consommés par le gate email existant.

**Tech Stack:** Odoo 19 CE, Python 3.12, WeasyPrint 68.1, QWeb, PostgreSQL.

## Global Constraints

- Syntaxe **Odoo 19** stricte : pas d'`attrs`, pas de `states`, pas de `t-esc` (utiliser `t-out`), `view_mode` = `list` jamais `tree`, pas de `_sql_constraints` (utiliser `models.Constraint`), pas de `self._context` / `self._cr` / `self._uid`.
- Préfixe des modules maison : `oski_` pour la boutique/blog OdooSkills.
- Version du manifeste : `19.0.1.0.0`.
- Chaînes d'interface en **français**.
- WeasyPrint épinglé à **68.1**. Import **jamais au niveau module** — toujours dans la méthode, avec message d'erreur explicite si absent (le module doit rester installable sans WeasyPrint).
- Vocabulaire : « guide PDF », **jamais « ebook »** (réservé à la ligne payante).
- Le module vit dans le sous-module `content/blog`, branche `feat/oski-article-pdf`. **Ne jamais commiter dans le dépôt parent** — une session Smartel y travaille en parallèle.
- Commande de test (le `--db-filter` est **obligatoire**, sinon les `HttpCase` renvoient 404) :

```bash
cd /home/stadev/vscode-projects/odoo19-dev
./venv/bin/python odoo/odoo-bin -c config/odoo_odooskills.conf \
  -d odooskills_test_artpdf --db-filter='^odooskills_test_artpdf$' \
  -i oski_article_pdf --test-enable --test-tags=/oski_article_pdf --stop-after-init
```

---

## Structure des fichiers

```
content/blog/modules/oski_article_pdf/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   ├── blog_post.py          # champs de suivi, hash source, déclenchement publication
│   ├── pdf_series.py         # post_ids ordonnés, génération série
│   └── pdf_renderer.py       # AbstractModel : HTML → octets PDF (WeasyPrint)
├── data/
│   ├── ir_cron.xml           # cron de génération (déclenché par _trigger)
│   └── mail_template_pdf.xml # email de livraison du guide
├── views/
│   ├── pdf_templates.xml     # gabarit QWeb : couverture, sommaire, contenu
│   ├── blog_post_views.xml   # champs + bouton dans le backend
│   └── pdf_series_views.xml
├── security/ir.model.access.csv
└── tests/
    ├── __init__.py
    ├── test_install.py
    ├── test_renderer.py
    ├── test_generate_post.py
    ├── test_generate_series.py
    ├── test_publish_trigger.py
    └── test_delivery.py
```

**Responsabilités.** `pdf_renderer.py` ne connaît que « HTML → PDF » : aucun savoir métier, testable seul. `blog_post.py` porte le cycle de vie (hash, péremption, déclenchement). `pdf_series.py` porte l'agrégation ordonnée. Le gabarit QWeb est le seul endroit qui connaît la mise en page.

---

## Task 1 : Squelette du module

**Files:**
- Create: `content/blog/modules/oski_article_pdf/__init__.py`
- Create: `content/blog/modules/oski_article_pdf/__manifest__.py`
- Create: `content/blog/modules/oski_article_pdf/models/__init__.py`
- Create: `content/blog/modules/oski_article_pdf/security/ir.model.access.csv`
- Test: `content/blog/modules/oski_article_pdf/tests/test_install.py`

**Interfaces:**
- Consumes: rien.
- Produces: module installable nommé `oski_article_pdf`, dépendant de `oski_lead_magnet`.

- [ ] **Step 1: Écrire le test d'installation**

`tests/__init__.py` :

```python
from . import test_install
```

`tests/test_install.py` :

```python
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestInstall(TransactionCase):
    def test_module_installed(self):
        module = self.env['ir.module.module'].search(
            [('name', '=', 'oski_article_pdf')], limit=1)
        self.assertTrue(module, "le module doit exister au registre")
        self.assertEqual(module.state, 'installed')
```

- [ ] **Step 2: Lancer le test, vérifier l'échec**

Run : la commande de test des Global Constraints.
Expected : FAIL — `oski_article_pdf` introuvable (le module n'existe pas encore).

- [ ] **Step 3: Écrire le squelette**

`__init__.py` :

```python
from . import models
```

`models/__init__.py` : (vide pour l'instant)

```python
```

`__manifest__.py` :

```python
{
    'name': 'OdooSkills - Guides PDF par article',
    'version': '19.0.1.0.0',
    'category': 'Website/Blog',
    'summary': "Génère un guide PDF soigné par article ou par série, livré contre email",
    'author': 'ADICOPS',
    'website': 'https://odooskills.com',
    'license': 'LGPL-3',
    'depends': ['oski_lead_magnet'],
    'data': [
        'security/ir.model.access.csv',
    ],
    'external_dependencies': {'python': ['weasyprint']},
    'installable': True,
    'application': False,
}
```

`security/ir.model.access.csv` :

```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_oski_pdf_series_user,oski.pdf.series user,oski_lead_magnet.model_oski_pdf_series,base.group_user,1,1,1,0
```

> `external_dependencies` fait échouer l'installation avec un message clair si WeasyPrint manque, au lieu d'un `ImportError` brut.

- [ ] **Step 4: Lancer le test, vérifier le succès**

Run : la commande de test des Global Constraints.
Expected : PASS, 1 test.

- [ ] **Step 5: Commit**

```bash
cd content/blog
git add modules/oski_article_pdf
git commit -m "feat(article-pdf): squelette du module oski_article_pdf"
```

---

## Task 2 : Champs de suivi et détection de péremption

**Files:**
- Create: `content/blog/modules/oski_article_pdf/models/blog_post.py`
- Modify: `content/blog/modules/oski_article_pdf/models/__init__.py`
- Test: `content/blog/modules/oski_article_pdf/tests/test_stale.py`

**Interfaces:**
- Consumes: `blog.post.oski_pdf_attachment_id`, `oski_pdf_series_id` (définis dans `oski_lead_magnet/models/blog_post.py`).
- Produces:
  - `blog.post.oski_series_seq` (Integer, défaut 10)
  - `blog.post.oski_pdf_generated_on` (Datetime)
  - `blog.post.oski_pdf_source_hash` (Char) — empreinte du contenu au moment de la génération
  - `blog.post._oski_source_hash() -> str` — empreinte courante
  - `blog.post.oski_pdf_stale` (Boolean, calculé, non stocké)

> **Pourquoi un hash et pas `write_date > generated_on`** : la génération écrit elle-même sur l'enregistrement, donc `write_date` devient postérieur à `generated_on` et **tout article serait éternellement périmé**. L'empreinte du contenu est la seule comparaison stable.

- [ ] **Step 1: Écrire le test qui échoue**

`tests/test_stale.py` :

```python
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestStale(TransactionCase):
    def setUp(self):
        super().setUp()
        blog = self.env['blog.blog'].create({'name': 'Blog test'})
        self.post = self.env['blog.post'].create({
            'name': 'Article test', 'blog_id': blog.id,
            'content': '<p>contenu initial</p>', 'is_published': True})

    def test_stale_when_never_generated(self):
        self.assertTrue(self.post.oski_pdf_stale)

    def test_not_stale_after_hash_recorded(self):
        self.post.oski_pdf_source_hash = self.post._oski_source_hash()
        self.post.oski_pdf_generated_on = '2026-07-19 10:00:00'
        self.assertFalse(self.post.oski_pdf_stale)

    def test_stale_after_content_change(self):
        self.post.oski_pdf_source_hash = self.post._oski_source_hash()
        self.post.oski_pdf_generated_on = '2026-07-19 10:00:00'
        self.post.content = '<p>contenu réécrit</p>'
        self.assertTrue(self.post.oski_pdf_stale)

    def test_title_change_also_makes_stale(self):
        self.post.oski_pdf_source_hash = self.post._oski_source_hash()
        self.post.oski_pdf_generated_on = '2026-07-19 10:00:00'
        self.post.name = 'Titre réécrit'
        self.assertTrue(self.post.oski_pdf_stale)
```

Ajouter à `tests/__init__.py` :

```python
from . import test_install
from . import test_stale
```

- [ ] **Step 2: Lancer le test, vérifier l'échec**

Run : commande de test des Global Constraints.
Expected : FAIL — `Invalid field 'oski_pdf_stale' on model 'blog.post'`.

- [ ] **Step 3: Implémenter**

`models/blog_post.py` :

```python
import hashlib

from odoo import api, fields, models


class BlogPost(models.Model):
    _inherit = 'blog.post'

    oski_series_seq = fields.Integer(
        string="Ordre dans la série", default=10,
        help="Ordre de lecture dans le guide combiné. La date de publication "
             "ne reflète pas toujours l'ordre pédagogique.")
    oski_pdf_generated_on = fields.Datetime(string="Guide PDF généré le", readonly=True)
    oski_pdf_source_hash = fields.Char(string="Empreinte source", readonly=True)
    oski_pdf_stale = fields.Boolean(
        string="Guide PDF périmé", compute='_compute_oski_pdf_stale')

    def _oski_source_hash(self):
        """Empreinte du contenu qui alimente le PDF."""
        self.ensure_one()
        raw = '%s|%s|%s' % (
            self.name or '', self.subtitle or '', str(self.content or ''))
        return hashlib.sha256(raw.encode('utf-8')).hexdigest()

    @api.depends('name', 'subtitle', 'content', 'oski_pdf_source_hash',
                 'oski_pdf_generated_on')
    def _compute_oski_pdf_stale(self):
        for post in self:
            if not post.oski_pdf_generated_on or not post.oski_pdf_source_hash:
                post.oski_pdf_stale = True
            else:
                post.oski_pdf_stale = (
                    post.oski_pdf_source_hash != post._oski_source_hash())
```

`models/__init__.py` :

```python
from . import blog_post
```

- [ ] **Step 4: Lancer le test, vérifier le succès**

Run : commande de test des Global Constraints.
Expected : PASS, 5 tests.

- [ ] **Step 5: Commit**

```bash
cd content/blog
git add modules/oski_article_pdf
git commit -m "feat(article-pdf): champs de suivi et péremption par empreinte de contenu"
```

---

## Task 3 : Moteur de rendu WeasyPrint

**Files:**
- Create: `content/blog/modules/oski_article_pdf/models/pdf_renderer.py`
- Modify: `content/blog/modules/oski_article_pdf/models/__init__.py`
- Test: `content/blog/modules/oski_article_pdf/tests/test_renderer.py`

**Interfaces:**
- Consumes: rien.
- Produces: AbstractModel `oski.pdf.renderer` avec
  - `_absolutize(html: str) -> str` — réécrit `src="/…"` et `href="/…"` en URL absolues d'après `web.base.url`
  - `_render_pdf(html: str) -> bytes` — octets PDF

- [ ] **Step 1: Écrire le test qui échoue**

`tests/test_renderer.py` :

```python
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestRenderer(TransactionCase):
    def setUp(self):
        super().setUp()
        self.renderer = self.env['oski.pdf.renderer']
        self.env['ir.config_parameter'].sudo().set_param(
            'web.base.url', 'https://odooskills.com')

    def test_absolutize_img_src(self):
        html = '<img src="/web/image/42"/>'
        self.assertIn('https://odooskills.com/web/image/42',
                      self.renderer._absolutize(html))

    def test_absolutize_leaves_external_untouched(self):
        html = '<img src="https://ailleurs.example/x.png"/>'
        self.assertEqual(self.renderer._absolutize(html), html)

    def test_absolutize_ignores_anchors(self):
        html = '<a href="#section">x</a>'
        self.assertEqual(self.renderer._absolutize(html), html)

    def test_render_produces_pdf_bytes(self):
        pdf = self.renderer._render_pdf(
            '<html><body><h1>Bonjour</h1></body></html>')
        self.assertTrue(pdf.startswith(b'%PDF'), "doit commencer par %PDF")
        self.assertGreater(len(pdf), 500)
```

Ajouter `from . import test_renderer` à `tests/__init__.py`.

- [ ] **Step 2: Lancer le test, vérifier l'échec**

Run : commande de test des Global Constraints.
Expected : FAIL — `KeyError: 'oski.pdf.renderer'`.

- [ ] **Step 3: Implémenter**

`models/pdf_renderer.py` :

```python
import logging
import re

from odoo import api, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

# src="/…" ou href="/…" mais PAS "//" (protocol-relative) ni "#ancre"
_REL_URL_RE = re.compile(r'(\s(?:src|href)=")(/(?!/))')


class OskiPdfRenderer(models.AbstractModel):
    _name = 'oski.pdf.renderer'
    _description = "Rendu HTML → PDF (WeasyPrint)"

    @api.model
    def _base_url(self):
        return self.env['ir.config_parameter'].sudo().get_param(
            'web.base.url', 'https://odooskills.com').rstrip('/')

    @api.model
    def _absolutize(self, html):
        """WeasyPrint n'a pas de contexte de session : les URL relatives
        doivent être résolues avant le rendu."""
        return _REL_URL_RE.sub(r'\g<1>%s/' % self._base_url(), html or '')

    @api.model
    def _render_pdf(self, html):
        """HTML complet → octets PDF."""
        try:
            from weasyprint import HTML
        except ImportError as err:
            raise UserError(
                "WeasyPrint n'est pas installé sur ce serveur. "
                "Installer les dépendances système (libpango-1.0-0, "
                "libpangoft2-1.0-0, libcairo2, libgdk-pixbuf-2.0-0) puis "
                "« pip install weasyprint==68.1 » dans le venv Odoo."
            ) from err
        return HTML(string=self._absolutize(html),
                    base_url=self._base_url()).write_pdf()
```

Ajouter `from . import pdf_renderer` à `models/__init__.py`.

- [ ] **Step 4: Lancer le test, vérifier le succès**

Run : commande de test des Global Constraints.
Expected : PASS, 9 tests cumulés.

- [ ] **Step 5: Commit**

```bash
cd content/blog
git add modules/oski_article_pdf
git commit -m "feat(article-pdf): moteur de rendu WeasyPrint isolé"
```

---

## Task 4 : Gabarit QWeb (couverture, contenu, sommaire)

**Files:**
- Create: `content/blog/modules/oski_article_pdf/views/pdf_templates.xml`
- Modify: `content/blog/modules/oski_article_pdf/__manifest__.py`
- Test: `content/blog/modules/oski_article_pdf/tests/test_template.py`

**Interfaces:**
- Consumes: rien.
- Produces: templates QWeb `oski_article_pdf.guide_document` (rendu avec `{'posts': recordset, 'title': str, 'subtitle': str, 'meta': str, 'is_series': bool}`).

> **Le CSS ci-dessous est celui validé par le rendu d'essai du 19/07.** Il tient compte de trois faits observés : WeasyPrint refuse `word-break: break-word` (utiliser `overflow-wrap`), le contenu des articles porte déjà son style inline, et `page-break-inside: avoid` sur un bloc très haut laisse un tiers de page blanc — d'où le seuil `max-height` au-delà duquel la coupure est autorisée.

- [ ] **Step 1: Écrire le test qui échoue**

`tests/test_template.py` :

```python
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestTemplate(TransactionCase):
    def setUp(self):
        super().setUp()
        blog = self.env['blog.blog'].create({'name': 'Développement Odoo'})
        self.post = self.env['blog.post'].create({
            'name': 'Mon article', 'blog_id': blog.id,
            'content': '<p>Corps de test</p>', 'is_published': True})

    def _render(self, is_series=False):
        return self.env['ir.qweb']._render('oski_article_pdf.guide_document', {
            'posts': self.post, 'title': 'Mon article', 'subtitle': 'Sous-titre',
            'meta': 'Développement Odoo · 2026-07-19', 'is_series': is_series})

    def test_contains_cover_and_content(self):
        html = str(self._render())
        self.assertIn('Mon article', html)
        self.assertIn('Corps de test', html)
        self.assertIn('GUIDE PDF', html.upper())

    def test_no_toc_for_single_article(self):
        self.assertNotIn('osk-toc', str(self._render(is_series=False)))

    def test_toc_present_for_series(self):
        self.assertIn('osk-toc', str(self._render(is_series=True)))

    def test_never_says_ebook(self):
        self.assertNotIn('ebook', str(self._render()).lower())
```

Ajouter `from . import test_template` à `tests/__init__.py`.

- [ ] **Step 2: Lancer le test, vérifier l'échec**

Run : commande de test des Global Constraints.
Expected : FAIL — template `oski_article_pdf.guide_document` introuvable.

- [ ] **Step 3: Implémenter le gabarit**

`views/pdf_templates.xml` :

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <template id="guide_document" name="Guide PDF OdooSkills">
        <html lang="fr">
        <head>
            <meta charset="utf-8"/>
            <title><t t-out="title"/></title>
            <style>
                @page { size: A4; margin: 18mm 16mm 20mm 16mm;
                    @bottom-center { content: "OdooSkills — " counter(page);
                        font-family: "DejaVu Sans", sans-serif; font-size: 8pt; color: #8a8398; } }
                @page :first { margin: 0; @bottom-center { content: ""; } }

                body { font-family: "DejaVu Serif", Georgia, serif; font-size: 10.5pt;
                    line-height: 1.55; color: #1a1a2e; orphans: 3; widows: 3; }

                .osk-cover { page-break-after: always; height: 297mm; background: #714B67;
                    color: #fff; padding: 45mm 20mm 20mm 20mm; box-sizing: border-box; }
                .osk-cover-kicker { font-family: "DejaVu Sans", sans-serif; font-size: 10pt;
                    letter-spacing: 3px; text-transform: uppercase; opacity: .75; margin-bottom: 14mm; }
                .osk-cover-title { font-size: 30pt; line-height: 1.18; font-weight: 700; margin: 0 0 8mm; }
                .osk-cover-sub { font-size: 13pt; line-height: 1.5; opacity: .88; margin-bottom: 24mm; }
                .osk-cover-meta { font-family: "DejaVu Sans", sans-serif; font-size: 9.5pt;
                    opacity: .8; border-top: 1px solid rgba(255,255,255,.35); padding-top: 5mm; }
                .osk-cover-brand { position: absolute; bottom: 18mm; left: 20mm;
                    font-family: "DejaVu Sans", sans-serif; font-size: 11pt; font-weight: 700; }

                .osk-toc { page-break-after: always; }
                .osk-toc h2 { border: none; }
                .osk-toc ol { padding-left: 6mm; }
                .osk-toc li { margin-bottom: 2mm; font-size: 11pt; }

                h1, h2, h3, h4 { font-family: "DejaVu Sans", sans-serif; color: #2b1b39;
                    page-break-after: avoid; page-break-inside: avoid; }
                h2 { font-size: 15pt; margin: 9mm 0 3mm; padding-bottom: 1.5mm;
                    border-bottom: 2px solid #714B67; }
                h3 { font-size: 12.5pt; margin: 6mm 0 2mm; }
                p { margin: 0 0 3mm; text-align: justify; }
                ul, ol { margin: 0 0 3mm; padding-left: 6mm; }
                a { color: #714B67; text-decoration: none; }

                pre { font-family: "DejaVu Sans Mono", monospace; font-size: 8pt;
                    line-height: 1.42; white-space: pre-wrap; overflow-wrap: break-word;
                    page-break-inside: avoid; max-height: 160mm; }
                code { font-family: "DejaVu Sans Mono", monospace; font-size: 8.5pt;
                    overflow-wrap: break-word; }

                table { width: 100%; border-collapse: collapse; margin: 3mm 0;
                    font-size: 9pt; page-break-inside: avoid; }
                th, td { border: 1px solid #d8d2dd; padding: 1.8mm 2.5mm;
                    text-align: left; vertical-align: top; }
                th { background: #f0ecf3; font-weight: 700; }
                img { max-width: 100%; height: auto; page-break-inside: avoid; }

                .alert { padding: 3mm 4mm; margin: 3mm 0; border: 1px solid #d8d2dd;
                    background: #faf8fb; page-break-inside: avoid; }
                .card { border: 1px solid #d8d2dd; padding: 3mm; margin: 3mm 0;
                    page-break-inside: avoid; }
                blockquote { margin: 3mm 0; padding: 2mm 0 2mm 4mm;
                    border-left: 3px solid #d8d2dd; font-style: italic; }
                .osk-article + .osk-article { page-break-before: always; }
            </style>
        </head>
        <body>
            <div class="osk-cover">
                <div class="osk-cover-kicker">Guide PDF · OdooSkills</div>
                <div class="osk-cover-title"><t t-out="title"/></div>
                <div class="osk-cover-sub"><t t-out="subtitle"/></div>
                <div class="osk-cover-meta"><t t-out="meta"/></div>
                <div class="osk-cover-brand">ODOOSKILLS</div>
            </div>

            <div t-if="is_series" class="osk-toc">
                <h2>Sommaire</h2>
                <ol>
                    <li t-foreach="posts" t-as="p"><t t-out="p.name"/></li>
                </ol>
            </div>

            <div t-foreach="posts" t-as="p" class="osk-article">
                <h1 t-if="is_series" t-out="p.name"/>
                <div t-out="p.content"/>
            </div>
        </body>
        </html>
    </template>
</odoo>
```

Ajouter à `__manifest__.py`, clé `data`, après la ligne security :

```python
        'views/pdf_templates.xml',
```

- [ ] **Step 4: Lancer le test, vérifier le succès**

Run : commande de test des Global Constraints.
Expected : PASS, 13 tests cumulés.

- [ ] **Step 5: Commit**

```bash
cd content/blog
git add modules/oski_article_pdf
git commit -m "feat(article-pdf): gabarit QWeb du guide (couverture, sommaire, contenu)"
```

---

## Task 5 : Génération pour un article seul

**Files:**
- Modify: `content/blog/modules/oski_article_pdf/models/blog_post.py`
- Test: `content/blog/modules/oski_article_pdf/tests/test_generate_post.py`

**Interfaces:**
- Consumes: `oski.pdf.renderer._render_pdf`, template `oski_article_pdf.guide_document`, `blog.post._oski_source_hash`.
- Produces: `blog.post._oski_generate_pdf() -> ir.attachment` — crée/remplace la pièce jointe, renseigne `oski_pdf_attachment_id`, `oski_pdf_generated_on`, `oski_pdf_source_hash`.

- [ ] **Step 1: Écrire le test qui échoue**

`tests/test_generate_post.py` :

```python
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestGeneratePost(TransactionCase):
    def setUp(self):
        super().setUp()
        blog = self.env['blog.blog'].create({'name': 'Développement Odoo'})
        self.post = self.env['blog.post'].create({
            'name': 'Article riche', 'blog_id': blog.id, 'is_published': True,
            'content': '<h2>Titre</h2><p>Texte</p><pre>ls -lah</pre>'
                       '<table><tr><td>a</td></tr></table>'})

    def test_generates_attachment(self):
        att = self.post._oski_generate_pdf()
        self.assertTrue(att, "doit renvoyer une pièce jointe")
        self.assertEqual(att.mimetype, 'application/pdf')
        self.assertEqual(self.post.oski_pdf_attachment_id, att)

    def test_attachment_is_a_real_pdf(self):
        import base64
        att = self.post._oski_generate_pdf()
        self.assertTrue(base64.b64decode(att.datas).startswith(b'%PDF'))

    def test_attachment_is_private(self):
        att = self.post._oski_generate_pdf()
        self.assertFalse(att.public, "le PDF ne doit pas être public (gate email)")

    def test_clears_stale_flag(self):
        self.post._oski_generate_pdf()
        self.assertFalse(self.post.oski_pdf_stale)
        self.assertTrue(self.post.oski_pdf_generated_on)

    def test_regeneration_replaces_previous_attachment(self):
        first = self.post._oski_generate_pdf()
        first_id = first.id
        self.post.content = '<p>réécrit</p>'
        second = self.post._oski_generate_pdf()
        self.assertNotEqual(second.id, first_id)
        self.assertFalse(self.env['ir.attachment'].browse(first_id).exists(),
                         "l'ancienne pièce jointe doit être supprimée")
```

Ajouter `from . import test_generate_post` à `tests/__init__.py`.

- [ ] **Step 2: Lancer le test, vérifier l'échec**

Run : commande de test des Global Constraints.
Expected : FAIL — `'blog.post' object has no attribute '_oski_generate_pdf'`.

- [ ] **Step 3: Implémenter**

Ajouter à `models/blog_post.py` (imports en tête du fichier) :

```python
import base64
import hashlib
import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)
```

Puis, dans la classe `BlogPost` :

```python
    def _oski_pdf_filename(self):
        self.ensure_one()
        slug = (self.name or 'guide').lower()
        slug = ''.join(c if c.isalnum() else '-' for c in slug).strip('-')
        while '--' in slug:
            slug = slug.replace('--', '-')
        return 'odooskills-%s.pdf' % slug[:60]

    def _oski_generate_pdf(self):
        """Rend le guide PDF de CET article et l'attache."""
        self.ensure_one()
        html = self.env['ir.qweb']._render('oski_article_pdf.guide_document', {
            'posts': self,
            'title': self.name or '',
            'subtitle': self.subtitle or '',
            'meta': '%s · %s · odooskills.com' % (
                self.blog_id.name or '',
                fields.Date.to_string(self.post_date) if self.post_date else ''),
            'is_series': False,
        })
        pdf_bytes = self.env['oski.pdf.renderer']._render_pdf(str(html))

        old = self.oski_pdf_attachment_id
        attachment = self.env['ir.attachment'].sudo().create({
            'name': self._oski_pdf_filename(),
            'datas': base64.b64encode(pdf_bytes),
            'mimetype': 'application/pdf',
            'res_model': 'blog.post',
            'res_id': self.id,
            'public': False,
        })
        self.write({
            'oski_pdf_attachment_id': attachment.id,
            'oski_pdf_generated_on': fields.Datetime.now(),
            'oski_pdf_source_hash': self._oski_source_hash(),
        })
        if old:
            old.sudo().unlink()
        _logger.info("Guide PDF généré pour l'article %s (%s o)", self.id, len(pdf_bytes))
        return attachment
```

- [ ] **Step 4: Lancer le test, vérifier le succès**

Run : commande de test des Global Constraints.
Expected : PASS, 18 tests cumulés.

- [ ] **Step 5: Commit**

```bash
cd content/blog
git add modules/oski_article_pdf
git commit -m "feat(article-pdf): génération du guide PDF d'un article"
```

---

## Task 6 : Génération pour une série ordonnée

**Files:**
- Create: `content/blog/modules/oski_article_pdf/models/pdf_series.py`
- Modify: `content/blog/modules/oski_article_pdf/models/__init__.py`
- Test: `content/blog/modules/oski_article_pdf/tests/test_generate_series.py`

**Interfaces:**
- Consumes: `oski.pdf.renderer._render_pdf`, template `oski_article_pdf.guide_document`.
- Produces:
  - `oski.pdf.series.post_ids` (One2many vers `blog.post` via `oski_pdf_series_id`)
  - `oski.pdf.series.subtitle` (Char), `generated_on` (Datetime)
  - `oski.pdf.series._oski_ordered_posts() -> recordset` — triés par `oski_series_seq` puis `post_date`
  - `oski.pdf.series._oski_generate_pdf() -> ir.attachment`

- [ ] **Step 1: Écrire le test qui échoue**

`tests/test_generate_series.py` :

```python
import base64

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestGenerateSeries(TransactionCase):
    def setUp(self):
        super().setUp()
        self.blog = self.env['blog.blog'].create({'name': 'Développement Odoo'})
        placeholder = self.env['ir.attachment'].create({
            'name': 'p.pdf', 'datas': base64.b64encode(b'%PDF-old'),
            'mimetype': 'application/pdf'})
        self.series = self.env['oski.pdf.series'].create({
            'name': 'Série Tech', 'attachment_id': placeholder.id})
        # créés dans le désordre exprès
        self.p2 = self._post('Deuxième', seq=20)
        self.p1 = self._post('Premier', seq=10)
        self.p3 = self._post('Troisième', seq=30)

    def _post(self, name, seq):
        return self.env['blog.post'].create({
            'name': name, 'blog_id': self.blog.id, 'is_published': True,
            'content': '<p>%s</p>' % name,
            'oski_pdf_series_id': self.series.id, 'oski_series_seq': seq})

    def test_post_ids_collects_members(self):
        self.assertEqual(len(self.series.post_ids), 3)

    def test_ordered_by_sequence_not_creation(self):
        self.assertEqual(
            self.series._oski_ordered_posts().mapped('name'),
            ['Premier', 'Deuxième', 'Troisième'])

    def test_generates_single_pdf_with_all_articles(self):
        att = self.series._oski_generate_pdf()
        self.assertEqual(att.mimetype, 'application/pdf')
        self.assertTrue(base64.b64decode(att.datas).startswith(b'%PDF'))
        self.assertEqual(self.series.attachment_id, att)
        self.assertTrue(self.series.generated_on)

    def test_series_pdf_is_private(self):
        att = self.series._oski_generate_pdf()
        self.assertFalse(att.public)

    def test_member_post_resolves_to_series_pdf(self):
        att = self.series._oski_generate_pdf()
        self.assertEqual(self.p1._oski_pdf_attachment(), att)
```

Ajouter `from . import test_generate_series` à `tests/__init__.py`.

- [ ] **Step 2: Lancer le test, vérifier l'échec**

Run : commande de test des Global Constraints.
Expected : FAIL — `Invalid field 'post_ids' on model 'oski.pdf.series'`.

- [ ] **Step 3: Implémenter**

`models/pdf_series.py` :

```python
import base64
import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class OskiPdfSeries(models.Model):
    _inherit = 'oski.pdf.series'

    post_ids = fields.One2many('blog.post', 'oski_pdf_series_id', string="Articles")
    subtitle = fields.Char(string="Sous-titre")
    generated_on = fields.Datetime(string="Généré le", readonly=True)

    def _oski_ordered_posts(self):
        self.ensure_one()
        return self.post_ids.sorted(
            key=lambda p: (p.oski_series_seq, p.post_date or fields.Datetime.now()))

    def _oski_generate_pdf(self):
        """Un SEUL rendu QWeb sur tous les articles ordonnés : pagination
        continue et sommaire cohérent (pas une concaténation de PDF)."""
        self.ensure_one()
        posts = self._oski_ordered_posts()
        if not posts:
            return self.env['ir.attachment']
        html = self.env['ir.qweb']._render('oski_article_pdf.guide_document', {
            'posts': posts,
            'title': self.name or '',
            'subtitle': self.subtitle or '',
            'meta': '%s articles · odooskills.com' % len(posts),
            'is_series': True,
        })
        pdf_bytes = self.env['oski.pdf.renderer']._render_pdf(str(html))

        old = self.attachment_id
        attachment = self.env['ir.attachment'].sudo().create({
            'name': 'odooskills-serie-%s.pdf' % self.id,
            'datas': base64.b64encode(pdf_bytes),
            'mimetype': 'application/pdf',
            'res_model': 'oski.pdf.series',
            'res_id': self.id,
            'public': False,
        })
        self.write({'attachment_id': attachment.id,
                    'generated_on': fields.Datetime.now()})
        posts.write({
            'oski_pdf_generated_on': fields.Datetime.now(),
        })
        for post in posts:
            post.oski_pdf_source_hash = post._oski_source_hash()
        if old:
            old.sudo().unlink()
        _logger.info("Guide PDF de série %s généré (%s articles, %s o)",
                     self.id, len(posts), len(pdf_bytes))
        return attachment
```

Ajouter `from . import pdf_series` à `models/__init__.py`.

- [ ] **Step 4: Lancer le test, vérifier le succès**

Run : commande de test des Global Constraints.
Expected : PASS, 23 tests cumulés.

- [ ] **Step 5: Commit**

```bash
cd content/blog
git add modules/oski_article_pdf
git commit -m "feat(article-pdf): génération du guide combiné d'une série ordonnée"
```

---

## Task 7 : Déclenchement à la publication (hors requête HTTP)

**Files:**
- Modify: `content/blog/modules/oski_article_pdf/models/blog_post.py`
- Create: `content/blog/modules/oski_article_pdf/data/ir_cron.xml`
- Modify: `content/blog/modules/oski_article_pdf/__manifest__.py`
- Test: `content/blog/modules/oski_article_pdf/tests/test_publish_trigger.py`

**Interfaces:**
- Consumes: `blog.post._oski_generate_pdf`, `oski.pdf.series._oski_generate_pdf`.
- Produces:
  - `blog.post.write()` surchargé — appelle `_trigger()` sur le cron au passage à publié ou à la modification du contenu d'un article publié
  - `blog.post._cron_generate_pending()` — génère les guides manquants ou périmés, triés par `visits` décroissant

> `ir.cron._trigger()` (présent en Odoo 19, `odoo/addons/base/models/ir_cron.py:666`) planifie l'exécution au prochain réveil du worker cron, indépendamment de `nextcall`. Le rendu WeasyPrint sort donc de la requête HTTP : la publication reste instantanée pour le rédacteur.

- [ ] **Step 1: Écrire le test qui échoue**

`tests/test_publish_trigger.py` :

```python
from unittest.mock import patch

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestPublishTrigger(TransactionCase):
    def setUp(self):
        super().setUp()
        self.blog = self.env['blog.blog'].create({'name': 'Développement Odoo'})

    def _make(self, published):
        return self.env['blog.post'].create({
            'name': 'Article', 'blog_id': self.blog.id,
            'content': '<p>x</p>', 'is_published': published})

    def test_publishing_triggers_cron(self):
        post = self._make(False)
        with patch('odoo.addons.base.models.ir_cron.ir_cron._trigger') as trig:
            post.is_published = True
            self.assertTrue(trig.called, "la publication doit déclencher le cron")

    def test_unpublishing_does_not_trigger(self):
        post = self._make(True)
        with patch('odoo.addons.base.models.ir_cron.ir_cron._trigger') as trig:
            post.is_published = False
            self.assertFalse(trig.called)

    def test_editing_published_post_triggers(self):
        post = self._make(True)
        with patch('odoo.addons.base.models.ir_cron.ir_cron._trigger') as trig:
            post.content = '<p>réécrit</p>'
            self.assertTrue(trig.called)

    def test_cron_generates_missing_pdf(self):
        post = self._make(True)
        self.assertTrue(post.oski_pdf_stale)
        self.env['blog.post']._cron_generate_pending()
        self.assertTrue(post.oski_pdf_attachment_id)
        self.assertFalse(post.oski_pdf_stale)

    def test_cron_skips_unpublished(self):
        post = self._make(False)
        self.env['blog.post']._cron_generate_pending()
        self.assertFalse(post.oski_pdf_attachment_id)

    def test_cron_isolates_failures(self):
        ok = self._make(True)
        broken = self._make(True)
        original = type(self.env['blog.post'])._oski_generate_pdf

        def selective(self_post):
            if self_post.id == broken.id:
                raise ValueError("rendu impossible")
            return original(self_post)

        with patch.object(type(self.env['blog.post']),
                          '_oski_generate_pdf', selective):
            self.env['blog.post']._cron_generate_pending()
        self.assertTrue(ok.oski_pdf_attachment_id,
                        "un article en échec ne doit pas interrompre la vague")
```

Ajouter `from . import test_publish_trigger` à `tests/__init__.py`.

- [ ] **Step 2: Lancer le test, vérifier l'échec**

Run : commande de test des Global Constraints.
Expected : FAIL — `_cron_generate_pending` inexistant, et aucun déclenchement.

- [ ] **Step 3: Implémenter**

Ajouter à la classe `BlogPost` dans `models/blog_post.py` :

```python
    # champs dont la modification rend le PDF obsolète
    _OSKI_PDF_SOURCE_FIELDS = {'name', 'subtitle', 'content', 'oski_pdf_series_id',
                               'oski_series_seq'}

    def write(self, vals):
        res = super().write(vals)
        becomes_published = vals.get('is_published') is True
        content_touched = bool(self._OSKI_PDF_SOURCE_FIELDS & set(vals))
        if becomes_published or content_touched:
            if any(p.is_published for p in self):
                self._oski_trigger_generation()
        return res

    def _oski_trigger_generation(self):
        """Planifie la génération hors requête HTTP."""
        cron = self.env.ref('oski_article_pdf.cron_generate_pdf',
                            raise_if_not_found=False)
        if cron:
            cron.sudo()._trigger()

    @api.model
    def _cron_generate_pending(self):
        """Génère les guides manquants ou périmés, les plus lus d'abord."""
        pending = self.search([('is_published', '=', True)]).filtered(
            lambda p: p.oski_pdf_stale)
        pending = pending.sorted(key=lambda p: p.visits or 0, reverse=True)
        for post in pending:
            try:
                if post.oski_pdf_series_id:
                    post.oski_pdf_series_id._oski_generate_pdf()
                else:
                    post._oski_generate_pdf()
                self.env.cr.commit()
            except Exception:
                self.env.cr.rollback()
                _logger.exception(
                    "Échec de génération du guide PDF pour l'article %s", post.id)
```

`data/ir_cron.xml` :

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo noupdate="1">
    <record id="cron_generate_pdf" model="ir.cron">
        <field name="name">OdooSkills — Génération des guides PDF</field>
        <field name="model_id" ref="website_blog.model_blog_post"/>
        <field name="state">code</field>
        <field name="code">model._cron_generate_pending()</field>
        <field name="interval_number">1</field>
        <field name="interval_type">days</field>
        <field name="active" eval="True"/>
    </record>
</odoo>
```

Ajouter `'data/ir_cron.xml',` à la clé `data` du manifeste.

- [ ] **Step 4: Lancer le test, vérifier le succès**

Run : commande de test des Global Constraints.
Expected : PASS, 29 tests cumulés.

- [ ] **Step 5: Commit**

```bash
cd content/blog
git add modules/oski_article_pdf
git commit -m "feat(article-pdf): génération déclenchée à la publication via ir.cron._trigger"
```

---

## Task 8 : Livraison par email et libellé série

**Files:**
- Create: `content/blog/modules/oski_article_pdf/data/mail_template_pdf.xml`
- Create: `content/blog/modules/oski_article_pdf/models/lead_capture.py`
- Modify: `content/blog/modules/oski_article_pdf/models/__init__.py`
- Modify: `content/blog/modules/oski_article_pdf/__manifest__.py`
- Modify: `content/blog/modules/oski_lead_magnet/views/pdf_gate_templates.xml`
- Test: `content/blog/modules/oski_article_pdf/tests/test_delivery.py`

**Interfaces:**
- Consumes: `oski.lead.capture._oski_capture_lead` (défini dans `oski_lead_magnet/models/lead_capture.py`), `blog.post._oski_pdf_gated_url`.
- Produces: envoi d'un email transactionnel contenant le lien tokenisé, après capture réussie.

- [ ] **Step 1: Écrire le test qui échoue**

`tests/test_delivery.py` :

```python
import base64

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestDelivery(TransactionCase):
    def setUp(self):
        super().setUp()
        blog = self.env['blog.blog'].create({'name': 'Développement Odoo'})
        self.post = self.env['blog.post'].create({
            'name': 'Article', 'blog_id': blog.id,
            'content': '<p>x</p>', 'is_published': True})
        self.post.oski_pdf_attachment_id = self.env['ir.attachment'].create({
            'name': 'g.pdf', 'datas': base64.b64encode(b'%PDF'),
            'mimetype': 'application/pdf', 'public': False})

    def _mails_to(self, email):
        return self.env['mail.mail'].sudo().search([('email_to', 'like', email)])

    def test_capture_sends_delivery_mail(self):
        self.env['oski.lead.capture'].sudo()._oski_capture_lead(
            'nouveau@example.com', True, 'pdf', self.post)
        self.assertTrue(self._mails_to('nouveau@example.com'),
                        "un email de livraison doit partir")

    def test_delivery_mail_contains_tokenized_link(self):
        self.env['oski.lead.capture'].sudo()._oski_capture_lead(
            'jeton@example.com', True, 'pdf', self.post)
        body = self._mails_to('jeton@example.com')[0].body_html or ''
        self.assertIn('access_token=', body)

    def test_existing_subscriber_still_gets_pdf(self):
        first = self.env['oski.lead.capture'].sudo()._oski_capture_lead(
            'connu@example.com', True, 'pdf', self.post)
        second = self.env['oski.lead.capture'].sudo()._oski_capture_lead(
            'connu@example.com', True, 'pdf', self.post)
        self.assertTrue(second['pdf_url'], "l'inscrit connu reçoit quand même son PDF")
        self.assertTrue(first['ok'] and second['ok'])

    def test_existing_subscriber_not_duplicated(self):
        for _ in range(2):
            self.env['oski.lead.capture'].sudo()._oski_capture_lead(
                'unique@example.com', True, 'pdf', self.post)
        contacts = self.env['mailing.contact'].sudo().search(
            [('email', '=ilike', 'unique@example.com')])
        self.assertEqual(len(contacts), 1)

    def test_no_mail_without_pdf(self):
        self.post.oski_pdf_attachment_id = False
        self.env['oski.lead.capture'].sudo()._oski_capture_lead(
            'sanspdf@example.com', True, 'pdf', self.post)
        self.assertFalse(self._mails_to('sanspdf@example.com'))
```

Ajouter `from . import test_delivery` à `tests/__init__.py`.

- [ ] **Step 2: Lancer le test, vérifier l'échec**

Run : commande de test des Global Constraints.
Expected : FAIL — aucun `mail.mail` créé.

- [ ] **Step 3: Implémenter**

`data/mail_template_pdf.xml` :

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo noupdate="1">
    <record id="mail_pdf_delivery" model="mail.template">
        <field name="name">OdooSkills — Livraison guide PDF</field>
        <field name="model_id" ref="website_blog.model_blog_post"/>
        <field name="subject">Votre guide PDF : {{ object.name }}</field>
        <field name="email_from">{{ user.company_id.email or 'odooers@odooskills.com' }}</field>
        <field name="body_html" type="html">
            <div style="font-family:Arial,sans-serif;font-size:14px;color:#1a1a2e">
                <p>Bonjour,</p>
                <p>Voici le guide PDF que vous avez demandé :
                   <strong t-out="object.name"/>.</p>
                <p>
                    <a t-att-href="ctx.get('pdf_url')"
                       style="display:inline-block;padding:12px 24px;background:#714B67;
                              color:#fff;text-decoration:none;border-radius:6px;font-weight:600">
                        Télécharger le guide PDF
                    </a>
                </p>
                <p style="color:#6b6478;font-size:12px">
                    Ce lien vous est personnel. Bonne lecture&#160;!<br/>
                    L'équipe OdooSkills — odooskills.com
                </p>
            </div>
        </field>
        <field name="auto_delete" eval="False"/>
    </record>
</odoo>
```

`models/lead_capture.py` :

```python
import logging

from odoo import api, models

_logger = logging.getLogger(__name__)


class OskiLeadCapture(models.AbstractModel):
    _inherit = 'oski.lead.capture'

    @api.model
    def _oski_capture_lead(self, email, consent, source, blog_post=None,
                           client_ip=None):
        result = super()._oski_capture_lead(
            email, consent, source, blog_post, client_ip=client_ip)
        if result.get('ok') and result.get('pdf_url') and blog_post:
            self._oski_send_pdf_mail(email, blog_post, result['pdf_url'])
        return result

    @api.model
    def _oski_send_pdf_mail(self, email, blog_post, pdf_url):
        """Copie par email du lien de téléchargement. Le téléchargement
        immédiat reste la voie principale : un échec d'envoi ne doit jamais
        casser la livraison."""
        template = self.env.ref('oski_article_pdf.mail_pdf_delivery',
                                raise_if_not_found=False)
        if not template:
            return
        base = self.env['ir.config_parameter'].sudo().get_param(
            'web.base.url', 'https://odooskills.com').rstrip('/')
        absolute = pdf_url if pdf_url.startswith('http') else base + pdf_url
        try:
            template.sudo().with_context(pdf_url=absolute).send_mail(
                blog_post.id, force_send=True,
                email_values={'email_to': email})
        except Exception:
            _logger.exception("Échec d'envoi du guide PDF à %s", email)
```

Ajouter `from . import lead_capture` à `models/__init__.py`, et `'data/mail_template_pdf.xml',` à la clé `data` du manifeste.

Modifier le libellé du bouton dans `oski_lead_magnet/views/pdf_gate_templates.xml`, template `pdf_gate_cta` — remplacer le bloc `<span>` et le `<button>` par :

```xml
            <t t-set="serie" t-value="blog_post.oski_pdf_series_id"/>
            <t t-set="nb" t-value="len(serie.post_ids) if serie else 0"/>
            <span class="fw-semibold d-block mb-2" style="color:#1a1a2e">
                📄 <t t-if="serie">Emportez toute la série en PDF</t>
                   <t t-else="">Emportez cet article en PDF</t>
            </span>
            <button type="button" class="btn btn-primary osk-pdf-btn">
                <t t-if="serie">Obtenir les <t t-out="nb"/> articles en PDF</t>
                <t t-else="">Obtenir cet article en PDF</t>
            </button>
```

- [ ] **Step 4: Lancer le test, vérifier le succès**

Run : commande de test des Global Constraints, **plus** la non-régression du module amont :

```bash
./venv/bin/python odoo/odoo-bin -c config/odoo_odooskills.conf \
  -d odooskills_test_artpdf --db-filter='^odooskills_test_artpdf$' \
  -u oski_lead_magnet --test-enable --test-tags=/oski_lead_magnet --stop-after-init
```

Expected : PASS, 34 tests cumulés pour `oski_article_pdf`, et les tests de `oski_lead_magnet` toujours verts.

- [ ] **Step 5: Commit**

```bash
cd content/blog
git add modules/oski_article_pdf modules/oski_lead_magnet
git commit -m "feat(article-pdf): livraison par email et libellé adapté aux séries"
```

---

## Task 9 : Retrait du popup

**Files:**
- Modify: `content/blog/modules/oski_lead_magnet/views/popup_templates.xml`
- Modify: `content/blog/modules/oski_lead_magnet/static/src/js/lead_popup.js:fin de fichier`
- Test: `content/blog/modules/oski_article_pdf/tests/test_no_popup.py`

**Interfaces:**
- Consumes: rien.
- Produces: plus aucun popup rendu ; le gate PDF reste intact.

- [ ] **Step 1: Écrire le test qui échoue**

`tests/test_no_popup.py` :

```python
import base64

from odoo.tests import HttpCase, tagged


@tagged('post_install', '-at_install')
class TestNoPopup(HttpCase):
    def setUp(self):
        super().setUp()
        self.blog = self.env['blog.blog'].create({'name': 'Développement Odoo'})
        self.post = self.env['blog.post'].create({
            'name': 'Article', 'blog_id': self.blog.id,
            'content': '<p>x</p>', 'is_published': True})
        self.post.oski_pdf_attachment_id = self.env['ir.attachment'].create({
            'name': 'g.pdf', 'datas': base64.b64encode(b'%PDF'),
            'mimetype': 'application/pdf', 'public': False})

    def test_popup_markup_absent(self):
        r = self.url_open('/blog/%s/%s' % (self.blog.id, self.post.id))
        self.assertNotIn('osk-lead-popup', r.text)

    def test_pdf_gate_still_present(self):
        r = self.url_open('/blog/%s/%s' % (self.blog.id, self.post.id))
        self.assertIn('osk-pdf-gate', r.text)
```

Ajouter `from . import test_no_popup` à `tests/__init__.py`.

- [ ] **Step 2: Lancer le test, vérifier l'échec**

Run : commande de test des Global Constraints.
Expected : FAIL sur `test_popup_markup_absent` — `osk-lead-popup` encore présent.

- [ ] **Step 3: Implémenter**

Dans `oski_lead_magnet/views/popup_templates.xml`, remplacer intégralement le template `lead_popup_inject` par une version neutralisée (garder l'identifiant pour ne pas casser les références) :

```xml
    <template id="lead_popup_inject" inherit_id="website.layout" name="Popup lead injection">
        <!-- Popup retiré le 19/07/2026 : la capture passe désormais par le
             gate PDF (module oski_article_pdf). Template conservé vide pour
             préserver l'identifiant et les données existantes. -->
        <xpath expr="//footer" position="after">
            <t/>
        </xpath>
    </template>
```

Dans `oski_lead_magnet/static/src/js/lead_popup.js`, remplacer le bloc final :

```javascript
onReady(function () {
    initPdfGate();
});
```

- [ ] **Step 4: Lancer le test, vérifier le succès**

Run : commande de test des Global Constraints, **plus** les tests amont de `oski_lead_magnet`.
Expected : PASS. Les tests de `oski_lead_magnet` référençant le popup (`test_popup_render.py`) doivent être adaptés — le popup n'est plus rendu, ce qui est le comportement attendu.

- [ ] **Step 5: Commit**

```bash
cd content/blog
git add modules/oski_lead_magnet modules/oski_article_pdf
git commit -m "feat(article-pdf): retrait du popup, la capture passe par le gate PDF"
```

---

## Task 10 : Backend — bouton de génération et vue série

**Files:**
- Create: `content/blog/modules/oski_article_pdf/views/blog_post_views.xml`
- Create: `content/blog/modules/oski_article_pdf/views/pdf_series_views.xml`
- Modify: `content/blog/modules/oski_article_pdf/models/blog_post.py`
- Modify: `content/blog/modules/oski_article_pdf/__manifest__.py`
- Test: `content/blog/modules/oski_article_pdf/tests/test_action.py`

**Interfaces:**
- Consumes: `blog.post._oski_generate_pdf`, `oski.pdf.series._oski_generate_pdf`.
- Produces: `blog.post.action_oski_generate_pdf()` — action multi-enregistrements pour la vague de rattrapage.

- [ ] **Step 1: Écrire le test qui échoue**

`tests/test_action.py` :

```python
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestAction(TransactionCase):
    def setUp(self):
        super().setUp()
        self.blog = self.env['blog.blog'].create({'name': 'Développement Odoo'})

    def _post(self, name, visits):
        return self.env['blog.post'].create({
            'name': name, 'blog_id': self.blog.id, 'is_published': True,
            'content': '<p>%s</p>' % name, 'visits': visits})

    def test_action_generates_for_all_selected(self):
        a, b = self._post('A', 10), self._post('B', 99)
        (a | b).action_oski_generate_pdf()
        self.assertTrue(a.oski_pdf_attachment_id)
        self.assertTrue(b.oski_pdf_attachment_id)

    def test_action_skips_unpublished(self):
        p = self._post('C', 5)
        p.is_published = False
        p.action_oski_generate_pdf()
        self.assertFalse(p.oski_pdf_attachment_id)
```

Ajouter `from . import test_action` à `tests/__init__.py`.

- [ ] **Step 2: Lancer le test, vérifier l'échec**

Run : commande de test des Global Constraints.
Expected : FAIL — `action_oski_generate_pdf` inexistant.

- [ ] **Step 3: Implémenter**

Ajouter à la classe `BlogPost` :

```python
    def action_oski_generate_pdf(self):
        """Action groupée : vague de rattrapage, les plus lus d'abord."""
        targets = self.filtered('is_published').sorted(
            key=lambda p: p.visits or 0, reverse=True)
        for post in targets:
            if post.oski_pdf_series_id:
                post.oski_pdf_series_id._oski_generate_pdf()
            else:
                post._oski_generate_pdf()
        return True
```

`views/blog_post_views.xml` :

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <record id="view_blog_post_form_oski_pdf" model="ir.ui.view">
        <field name="name">blog.post.form.oski.article.pdf</field>
        <field name="model">blog.post</field>
        <field name="inherit_id" ref="website_blog.view_blog_post_form"/>
        <field name="arch" type="xml">
            <xpath expr="//field[@name='name']" position="after">
                <field name="oski_series_seq"/>
                <field name="oski_pdf_generated_on" readonly="1"/>
                <field name="oski_pdf_stale" readonly="1"/>
            </xpath>
        </field>
    </record>

    <record id="action_generate_guide_pdf" model="ir.actions.server">
        <field name="name">Générer le guide PDF</field>
        <field name="model_id" ref="website_blog.model_blog_post"/>
        <field name="binding_model_id" ref="website_blog.model_blog_post"/>
        <field name="binding_view_types">list,form</field>
        <field name="state">code</field>
        <field name="code">records.action_oski_generate_pdf()</field>
    </record>
</odoo>
```

`views/pdf_series_views.xml` :

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <record id="view_oski_pdf_series_form" model="ir.ui.view">
        <field name="name">oski.pdf.series.form</field>
        <field name="model">oski.pdf.series</field>
        <field name="arch" type="xml">
            <form string="Série de guides PDF">
                <sheet>
                    <group>
                        <field name="name"/>
                        <field name="subtitle"/>
                        <field name="attachment_id"/>
                        <field name="generated_on" readonly="1"/>
                    </group>
                    <field name="post_ids">
                        <list string="Articles">
                            <field name="oski_series_seq"/>
                            <field name="name"/>
                            <field name="visits"/>
                            <field name="oski_pdf_stale"/>
                        </list>
                    </field>
                </sheet>
            </form>
        </field>
    </record>
</odoo>
```

Ajouter au manifeste, clé `data` :

```python
        'views/blog_post_views.xml',
        'views/pdf_series_views.xml',
```

- [ ] **Step 4: Lancer le test, vérifier le succès**

Run : commande de test des Global Constraints.
Expected : PASS, 38 tests cumulés.

- [ ] **Step 5: Commit**

```bash
cd content/blog
git add modules/oski_article_pdf
git commit -m "feat(article-pdf): bouton de génération groupée et vue série"
```

---

## Task 11 : Contrôle visuel avant déploiement

**Files:**
- Aucun fichier de code. Vérification manuelle obligatoire — un test automatisé ne peut pas juger une mise en page.

- [ ] **Step 1: Générer trois guides représentatifs en local**

Sur la base de test, générer :
- un article très codé (le plus dense disponible),
- un article de prose avec images,
- une série complète.

```bash
./venv/bin/python odoo/odoo-bin shell -c config/odoo_odooskills.conf \
  -d odooskills_test_artpdf --no-http
```

```python
posts = env['blog.post'].search([('is_published', '=', True)], limit=3)
for p in posts:
    att = p._oski_generate_pdf()
    open('/tmp/guide_%s.pdf' % p.id, 'wb').write(base64.b64decode(att.datas))
    print(p.id, p.name)
env.cr.commit()
```

- [ ] **Step 2: Inspecter les pages**

```bash
for f in /tmp/guide_*.pdf; do pdftoppm -png -r 90 "$f" "${f%.pdf}"; done
```

Contrôler, page par page :
- couverture pleine page, sans numéro de page ;
- aucun bloc de code coupé en deux entre deux pages ;
- **aucune page à moins de la moitié remplie** — c'est le défaut connu du `page-break-inside: avoid` sur les gros blocs ; si présent, ajuster le seuil `max-height` du gabarit ;
- images présentes et non débordantes ;
- tables non tronquées à droite.

- [ ] **Step 3: Corriger le gabarit si nécessaire, puis commiter**

```bash
cd content/blog
git add modules/oski_article_pdf/views/pdf_templates.xml
git commit -m "fix(article-pdf): ajustement du gabarit après contrôle visuel"
```

---

## Task 12 : Déploiement production

> **HALT — étape à faire valider explicitement avant exécution.** Elle installe des paquets système sur le VPS de production et génère 121 PDF.

**Files:** aucun. Opérations sur `ssh bodoo19`, DB `Odooskills`.

- [ ] **Step 1: Installer les dépendances système**

```bash
ssh bodoo19 'sudo apt update && sudo apt install -y \
  libpango-1.0-0 libpangoft2-1.0-0 libcairo2 libgdk-pixbuf-2.0-0'
```

Repli en cas de problème : `sudo apt remove` des mêmes paquets.

- [ ] **Step 2: Installer WeasyPrint dans le venv Odoo**

```bash
ssh bodoo19 'sudo -u odoo19 /opt/odoo19/odoo-venv/bin/pip install weasyprint==68.1'
ssh bodoo19 '/opt/odoo19/odoo-venv/bin/python3 -c "import weasyprint; print(weasyprint.__version__)"'
```

Expected : `68.1`.

- [ ] **Step 3: Déployer le module**

```bash
rsync -a content/blog/modules/oski_article_pdf/ bodoo19:/tmp/oski_article_pdf/
ssh bodoo19 'sudo rm -rf /opt/odoo19/odoo-custom-addons/oski_article_pdf && \
  sudo cp -r /tmp/oski_article_pdf /opt/odoo19/odoo-custom-addons/oski_article_pdf && \
  sudo chown -R odoo19:odoo19 /opt/odoo19/odoo-custom-addons/oski_article_pdf'
ssh bodoo19 'sudo systemctl stop odoo19 && \
  sudo -u odoo19 /opt/odoo19/odoo-venv/bin/python3 /opt/odoo19/odoo/odoo-bin \
    -c /etc/odoo19.conf -d Odooskills -i oski_article_pdf --stop-after-init && \
  sudo systemctl start odoo19'
```

- [ ] **Step 4: Première vague, les plus lus d'abord**

Générer par lots de 20 pour surveiller la charge et le filestore :

```python
posts = env['blog.post'].search([('is_published', '=', True)])
posts = posts.sorted(key=lambda p: p.visits or 0, reverse=True)[:20]
posts.action_oski_generate_pdf()
env.cr.commit()
```

- [ ] **Step 5: Vérifier en ligne**

```bash
curl -sL "https://odooskills.com/blog/<blog>/<id>" | grep -c "osk-pdf-gate"
```

Expected : ≥ 1 sur un article traité, et le bouton porte le libellé « Obtenir cet article en PDF » ou « Obtenir les N articles en PDF ».

Contrôler enfin la taille du filestore :

```bash
ssh bodoo19 'sudo du -sh /opt/odoo19/.local/share/Odoo/filestore/Odooskills'
```

---

## Auto-revue

**Couverture du spec.** §3 moteur → Task 3. §4 infra → Task 12. §5 modèle → Tasks 2 et 6. §6 gabarit → Task 4, seuil de hauteur contrôlé en Task 11. §7 génération → Tasks 5, 6, 7, 10. §8 livraison → Task 8. §9 retrait popup → Task 9. §10 tests → répartis, chaque tâche portant les siens. §12 risques : `apt` (Task 12 sous HALT), SPF/DKIM (le téléchargement immédiat reste la voie principale, Task 8), blancs de page (Task 11), filestore (Task 12 step 5), articles atypiques (`test_cron_isolates_failures`, Task 7).

**Écart assumé.** Le spec évoquait un cron « filet de sécurité » périodique ; il est implémenté comme cron quotidien qui sert aussi de cible à `_trigger()` — un seul objet cron pour les deux usages, plutôt que deux.

**Cohérence des noms.** `_oski_generate_pdf` (article et série), `_oski_source_hash`, `_oski_ordered_posts`, `_oski_trigger_generation`, `_cron_generate_pending`, `action_oski_generate_pdf`, `_render_pdf`, `_absolutize` — vérifiés identiques entre définition et appels.

"""Règles de nettoyage des repères de série (tools/markers.py).

Les extraits viennent de l'instantané de production (articles cités en commentaire),
raccourcis autour de la structure dont dépend chaque règle."""
from odoo.tests import BaseCase, tagged

import json
import os
import re
from html.parser import HTMLParser

from odoo.addons.oski_blog_series.tools import markers, markers_curated
from odoo.addons.oski_blog_series.tools.markers import Edit

BODY = '<section class="s_text_block pt32 pb32"><p>Contenu de l\'article.</p></section>\n'

# Article 45 : navigation seule, légende « Suite de la Saison » coupée par <strong>
NAV_45 = """<section class="s_text_block pt32 pb24">
    <div class="container">
        <div class="row">
            <div class="col-lg-10 mx-auto">
                <p class="text-muted small text-center mb-3">
                    Suite de la <strong>Saison 2 — Acheter & Vendre</strong>
                </p>
                <div class="d-flex justify-content-between align-items-center border-top pt-4">
                    <a href="/blog/fonctionnel-odoo-1/les-achats-dans-odoo-19-fournisseurs-commandes-et-reception-44" class="btn btn-outline-secondary">&larr; Les achats</a>
                    <a href="/blog/fonctionnel-odoo-1/le-crm-dans-odoo-19-pipeline-leads-et-opportunites-46" class="btn btn-outline-primary">Le CRM &rarr;</a>
                </div>
            </div>
        </div>
    </div>
</section>"""

# Article 61 : navigation seule avec codes T
NAV_61 = """<section class="s_text_block pt32 pb24">
    <div class="container">
        <div class="row">
            <div class="col-lg-10 mx-auto">
                <div class="d-flex justify-content-between align-items-center border-top pt-4">
                    <a href="/blog/developpement-odoo-2/attributs-de-modeles-odoo-19-order-rec-name-constraint-60" class="btn btn-outline-secondary">
                        &larr; T09 — Attributs de modèles
                    </a>
                    <a href="/blog/developpement-odoo-2/relations-entre-modeles-odoo-19-many2one-one2many-many2many-62" class="btn btn-outline-primary">
                        T11 — Relations entre modèles &rarr;
                    </a>
                </div>
            </div>
        </div>
    </div>
</section>"""

# Article 133 : navigation Tech-Email avec légende « Série … — Article x/y — … »
NAV_133 = """<section class="pt-4 pb-4">
        <div class="d-flex justify-content-between flex-wrap gap-2">
          <a href="/blog/developpement-odoo-2/mailaliasdomain-en-odoo-19-bounce-catchall-et-default-from-par-societe-132" class="btn btn-outline-secondary">← Précédent — mail.alias.domain</a>
          <a href="/blog/developpement-odoo-2/mailthread-en-odoo-19-followers-sous-types-et-notifications-du-chatter-135" class="btn btn-outline-primary">Suivant — mail.thread &amp; followers &rarr;</a>
        </div>
        <p class="text-muted small mt-2 text-center">
          <em>Série Tech-Email — Article 6/14 — Parcours Infrastructure emailing Odoo 19.</em>
        </p>
      </section>"""

# Article 111 : « Article précédent » / « Article suivant F11·2 — … »
NAV_111 = """<section class="s_cta_box pt32 pb32 oe_structure_solo">
  <div class="container">
    <div class="row">
      <div class="col-lg-10 mx-auto">
        <div class="d-flex justify-content-between flex-wrap gap-2">
          <a class="btn btn-outline-secondary disabled" aria-disabled="true">← Article précédent <small>(ouverture de saison)</small></a>
          <a class="btn btn-outline-primary" href="/blog/fonctionnel-odoo-1/taches-dependances-suivi-en-odoo-ce-et-ce-qui-demande-ee-112">Article suivant F11·2 — Tâches, dépendances &amp; suivi en Odoo CE →</a>
        </div>
      </div>
    </div>
  </div>
</section>"""

# Article 169 : navigation Licences, bandeau « · 1/3 » à l'intérieur
NAV_169 = """<section class="s_text_block pt24 pb32">
    <div class="container">
        <div class="row">
            <div class="col-lg-10 mx-auto">
                <p class="text-uppercase small text-muted mb-2">Série « Licences &amp; distribution » · 1/3</p>
                <div class="d-flex justify-content-between align-items-center">
                    <span class="btn btn-outline-secondary disabled">← Début de la série</span>
                    <a href="/blog/developpement-odoo-2/manifest-py-odoo-19-decrypte-170" class="btn btn-outline-primary">2/3 &mdash; <code>__manifest__.py</code> décrypté →</a>
                </div>
            </div>
        </div>
    </div>
</section>"""
EYEBROW_169 = '<p class="text-uppercase small mb-2 text-warning">Série « Licences &amp; distribution » · Article 1/3</p>'

# Article 52 : CTA guide + bloc de liens dans la même section
NAV_CTA_52 = """<section class="s_text_block pt48 pb48">
    <div class="container">
        <div class="row">
            <div class="col-lg-8 mx-auto text-center">
                <div class="s_card p-4 bg-primary text-white rounded">
                    <h3>Télécharge le Guide Technique Odoo 19</h3>
                    <p class="mt-2">Architecture, pièges v19, checklist premier module — tout dans un PDF gratuit.</p>
                    <a href="/guide-technique-odoo" class="btn btn-light btn-lg mt-2" target="_blank">
                        Télécharger le guide
                    </a>
                </div>

                <div class="mt-4">
                    <p class="text-muted">
                        <a href="/blog/developpement-odoo-2/installer-odoo-19-sur-ubuntu-2404-lts-50" class="btn btn-outline-secondary me-2">
                            &larr; Installer sur Ubuntu
                        </a>
                        Article suivant de la série :
                        <a href="/blog/developpement-odoo-2/installer-odoo-19-avec-docker-53" class="btn btn-outline-primary ms-2">
                            Installer avec Docker &rarr;
                        </a>
                    </p>
                </div>
            </div>
        </div>
    </div>
</section>"""

# Article 61 : « Prochain article — T11 » + résumé
NEXT_61 = """<section class="s_text_block pt48 pb48 bg-dark text-white text-center">
    <div class="container">
        <div class="row">
            <div class="col-lg-8 mx-auto">
                <h2 class="text-white">Prochain article — T11</h2>
                <p class="lead text-light">On aborde les <strong>champs relationnels</strong> :
                    <code>Many2one</code>, <code>One2many</code>, <code>Many2many</code>.
                    Comment relier les modèles entre eux et quand utiliser chaque type de relation.</p>
                <a href="/guide-technique-odoo" class="btn btn-warning btn-lg mt-3">
                    Télécharger le guide technique Odoo 19 (PDF gratuit)
                </a>
            </div>
        </div>
    </div>
</section>"""

# Article 41 : lien précédent + « Prochain article » avec résumé dans la même section
NEXT_41 = """<section class="s_text_block pt32 pb32 o_cc o_cc5" data-snippet="s_text_block" data-name="Navigation articles">
    <div class="container s_allow_columns text-center">
        <p><a href="/blog/fonctionnel-odoo-1/configurer-linventaire-dans-odoo-19-entrepot-produits-et-stock-initial-40" class="text-white-75">← Article précédent : Configurer l'inventaire</a></p>
        <h2 class="text-white">Prochain article</h2>
        <p class="lead text-white-75">La <strong>traçabilité par lots et numéros de série</strong> — comment suivre chaque laptop par son numéro de série et chaque carton de SSD par lot.</p>
        <p><a href="/blog/fonctionnel-odoo-1/tracabilite-par-lots-et-numeros-de-serie-dans-odoo-19-42" class="btn btn-outline-light btn-lg">Article 3 : Traçabilité lots/séries →</a></p>
    </div>
</section>"""

# Article 145 : encadré « formations » (liens « Découvrir → », pas de navigation)
FORMATIONS_145 = ('<section class="s_text_block pt8 pb24" data-oski-ebook-cta="1"><div class="container"><div class="row">'
                  '<div class="col-lg-10 mx-auto"><div class="o_oski_ebook_cta p-4 rounded">'
                  '<p class="mb-3 fw-bold" style="color:#1a1a2e">📘 Pour aller plus loin : nos formations Odoo 19</p>'
                  '<div class="d-flex flex-column flex-md-row gap-3">'
                  '<a href="/shop/ebook-e1-formation-technique-odoo-19-ebook-3" class="d-flex"><span>'
                  '<span class="d-block fw-semibold">Formation Technique Odoo 19 (ebook)</span>'
                  '<span class="small text-primary">Découvrir →</span></span></a>'
                  '<a href="/shop/ebook-e3-formation-deploiement-odoo-19-ebook-5" class="d-flex"><span>'
                  '<span class="d-block fw-semibold">Formation Déploiement Odoo 19 (ebook)</span>'
                  '<span class="small text-primary">Découvrir →</span></span></a>'
                  '</div></div></div></div></div></section>')

# Article 155 : « Continuer la Saison Restaurant » (phrase + liens)
RESTAURANT_155 = """<section class="s_cta_box pt48 pb48 bg-primary text-white">
    <div class="container text-center">
        <h2>Continuer la Saison Restaurant</h2>
        <p class="lead">Le plan de salle est dessiné. Reprends depuis la configuration initiale, ou
            complète ta maîtrise du Point de vente Odoo&nbsp;19.</p>
        <div class="mt-4">
            <a href="/blog/fonctionnel-odoo-1/configurer-la-gestion-de-restaurant-dans-odoo-19-community-154" class="btn btn-light btn-lg me-2 mb-2">
                &larr; Configurer la gestion de restaurant
            </a>
            <a href="/blog/fonctionnel-odoo-1/installer-configurer-pos-odoo-87" class="btn btn-outline-light btn-lg mb-2">
                Installer et configurer le POS &rarr;
            </a>
        </div>
    </div>
</section>"""

# Article 65 : « Voir aussi dans cette série »
SEE_ALSO_65 = """<section class="s_text_block pt32 pb32 bg-light">
    <div class="container">
        <div class="row">
            <div class="col-lg-10 mx-auto">
                <h3>Voir aussi dans cette série</h3>
                <div class="row mt-3">
                    <div class="col-md-4">
                        <div class="s_card p-3 text-center">
                            <p class="mb-1"><strong><a href="/blog/developpement-odoo-2/relations-entre-modeles-odoo-19-many2one-one2many-many2many-62">T11 — Relations entre modèles</a></strong></p>
                            <p class="small text-muted">Many2one, One2many, Many2many</p>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="s_card p-3 text-center">
                            <p class="mb-1"><strong><a href="/blog/developpement-odoo-2/contraintes-et-champs-calcules-odoo-19-apidepends-modelsconstraint-63">T12 — Contraintes et champs calculés</a></strong></p>
                            <p class="small text-muted">@api.depends, models.Constraint</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</section>"""

# Article 172 : « La série — » seule (titre, liste, phrase)
SERIES_172 = """<section class="s_text_block pt8 pb24">
    <div class="container">
        <div class="row">
            <div class="col-lg-10 mx-auto">
                <h3>La série — Reprendre ses données dans Odoo 19</h3>
                <ul>
                    <li><strong>Article 1/5 — Importer clients et fournisseurs</strong> — tu y es.</li>
                    <li>Article 2/5 — Importer son catalogue articles.</li>
                    <li>Article 3/5 — Charger son stock initial.</li>
                    <li>Article 4/5 — Reprendre sa balance d'ouverture.</li>
                    <li>Article 5/5 — Recetter sa reprise de données.</li>
                </ul>
                <p>Chaque article reprend la base du précédent, dans l'ordre des dépendances réelles d'une
                    reprise&nbsp;: les tiers, puis les articles, puis le stock qui référence les articles, puis
                    la comptabilité qui référence les tiers.</p>
            </div>
        </div>
    </div>
</section>"""

# Article 165 : « La série Traduction » + « Côté fonctionnel » dans la même section
SERIES_165_LIST = """<h3>La série Traduction — volet technique</h3>
                <ul>
                    <li><strong>1. Ajouter une langue, traduire l'interface et les rapports</strong> — tu y es.</li>
                    <li>2. Traduire ton propre module (<code>.po</code>, <code>_()</code>) vers l'arabe, et
                        traduire par Python — <a href="/blog/developpement-odoo-2/traduire-son-propre-module-odoo-19-vers-larabe-166">à lire</a>.</li>
                </ul>"""
SERIES_165 = """<section class="s_text_block pt8 pb24">
    <div class="container">
        <div class="row">
            <div class="col-lg-10 mx-auto">
                """ + SERIES_165_LIST + """
                <h3 class="mt-4">Côté fonctionnel, sans écrire de code</h3>
                <p>Le même sujet, vu du métier&nbsp;: la série jumelle sur le
                    <a href="/blog/fonctionnel-odoo-1">blog Fonctionnel</a> traite de
                    <a href="/blog/fonctionnel-odoo-1/traduire-ton-odoo-19-sans-ecrire-une-ligne-de-code-167">traduire
                    sans coder</a>.</p>
            </div>
        </div>
    </div>
</section>"""

# Article 173 : titre + liste + phrase précédent / suivant
SERIES_173 = """<section class="s_text_block pt8 pb24">
    <div class="container">
        <div class="row">
            <div class="col-lg-10 mx-auto">
                <h3>La série — Reprendre ses données dans Odoo 19</h3>
                <ul>
                    <li>Article 1/5 — Importer clients et fournisseurs.</li>
                    <li><strong>Article 2/5 — Importer son catalogue articles</strong> — tu y es.</li>
                    <li>Article 3/5 — Charger son stock initial.</li>
                    <li>Article 4/5 — Reprendre sa balance d'ouverture.</li>
                    <li>Article 5/5 — Recetter sa reprise de données.</li>
                </ul>
                <p class="mb-0"><strong>Article&nbsp;2/5</strong> — précédent&nbsp;:
                    <em>Importer clients et fournisseurs dans Odoo 19 Community</em>. Suivant&nbsp;:
                    <em>Charger son stock initial dans Odoo 19 Community</em>.</p>
            </div>
        </div>
    </div>
</section>"""

# Article 171 : grille de cartes « La série » avec une carte hors série
SERIES_171 = """<section class="s_features_grid pt32 pb32">
    <div class="container">
        <div class="row">
            <div class="col-lg-10 mx-auto">
                <h3 class="text-center mb-4">La série « Licences &amp; distribution »</h3>
                <div class="row">
                    <div class="col-md-4">
                        <div class="s_card p-3 h-100">
                            <h5><a href="/blog/developpement-odoo-2/quelle-licence-pour-votre-module-odoo-19-169">1/3 — Quelle licence pour votre module ?</a></h5>
                            <p class="small">Les 10 valeurs, la règle de contamination AGPL, et pourquoi une licence ne protège rien techniquement.</p>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="s_card p-3 h-100">
                            <h5><a href="/blog/developpement-odoo-2/manifest-py-odoo-19-decrypte-170">2/3 — <code>__manifest__.py</code> décrypté</a></h5>
                            <p class="small">Les 33 clés, la version qui rend un module invisible, les 3 formes d'<code>auto_install</code>.</p>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="s_card p-3 h-100">
                            <h5><a href="/blog/developpement-odoo-2/architecture-technique-odoo-56">Architecture technique Odoo 19</a></h5>
                            <p class="small">Le socle sur lequel tout module se greffe — utile avant de vendre quoi que ce soit.</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</section>"""

# Article 61 : code T dans un bloc de code (commentaire Python)
PRE_61 = ('<pre class="language-python"><code class="language-python">'
          '    # ── Champs non-relationnels (T10) ─────────────────────────────────────────\n'
          '    deadline = fields.Date(string=\'Échéance\', tracking=True)</code></pre>')
LINK_T09_61 = '<a href="/blog/developpement-odoo-2/attributs-de-modeles-odoo-19-order-rec-name-constraint-60">T09 — Attributs de modèles</a>'
LINK_T11_65 = '<a href="/blog/developpement-odoo-2/relations-entre-modeles-odoo-19-many2one-one2many-many2many-62">T11</a>'


@tagged('post_install', '-at_install')
class TestMarkersEyebrow(BaseCase):

    def test_eyebrow_keeps_theme(self):
        cases = [
            # (article, bandeau, texte attendu)
            (65, 'Bloc 3 · Framework ORM — Article 7/8', 'Framework ORM'),
            (70, 'Bloc 4 · Interface utilisateur — Article 4/4 · Fin du Bloc 4', 'Interface utilisateur'),
            (74, 'Bloc 5 · Article 4/4 — Clôture du Parcours Fondamentaux', 'Clôture du Parcours Fondamentaux'),
            (80, 'Saison 5 · Article 4/6 — Site Web, eCommerce &amp; Engagement', 'Site Web, eCommerce &amp; Engagement'),
            (155, 'Saison Restaurant · Article 2/6 — Hub Point de vente', 'Hub Point de vente'),
            (51, 'Fin de la Saison 3 — Compta &amp; Production', 'Compta &amp; Production'),
        ]
        for post_id, before, after in cases:
            with self.subTest(post=post_id):
                old = '<p class="text-uppercase small mb-2 text-warning">%s</p>' % before
                self.assertEqual(markers.eyebrow_edits(BODY + old, 'Nom de série'), [
                    Edit('R1', old, '<p class="text-uppercase small mb-2 text-warning">%s</p>' % after, False)])

    def test_eyebrow_without_theme_uses_escaped_series_name(self):
        cases = [
            (149, '<p class="text-uppercase small mb-2 text-warning">Série Rapports Excel · Article 2/6</p>'),
            (109, '<p class="text-uppercase small mb-2 text-warning">Saison « Dépassement tech v19 » · Article 5/5 · CLOSING</p>'),
            (47, '<p class="text-uppercase small mb-2 text-warning">Saison 3 · Article 2/4</p>'),
            (171, '<p class="text-uppercase small text-muted mb-2">Série « Licences &amp; distribution » · 3/3 — fin</p>'),
            (160, '<p class="text-uppercase small mb-2" style="color:#f06595">Série Rapports PDF · Article 1/5</p>'),
        ]
        for post_id, old in cases:
            with self.subTest(post=post_id):
                opening = old[:old.index('>') + 1]
                self.assertEqual(markers.eyebrow_edits(old + BODY, 'Compta & <Production>'), [
                    Edit('R1', old, opening + 'Compta &amp; &lt;Production&gt;</p>', False)])

    def test_two_numbered_eyebrows_are_both_cleaned(self):
        # Article 47 : bandeau d'ouverture + bandeau du CTA « article suivant »
        first = '<p class="text-uppercase small mb-2 text-warning">Saison 3 · Article 1/4 — Compta &amp; Production</p>'
        second = '<p class="text-uppercase small mb-2 text-warning">Saison 3 · Article 2/4</p>'
        html = ('<section class="s_banner"><div class="container">%s<h1>La comptabilité dans Odoo 19</h1></div></section>\n'
                '<section class="s_cta_box pt48 pb48 bg-dark text-white o_colored_level">\n    <div class="container text-center">\n'
                '        %s\n        <h2>Article 9 — Facturation &amp; paiements dans Odoo 19</h2>\n    </div>\n</section>') % (first, second)
        self.assertEqual(markers.eyebrow_edits(html, 'Comptabilité et production'), [
            Edit('R1', first, '<p class="text-uppercase small mb-2 text-warning">Compta &amp; Production</p>', False),
            Edit('R1', second, '<p class="text-uppercase small mb-2 text-warning">Comptabilité et production</p>', False),
        ])

    def test_eyebrow_without_expected_class_is_proposed_for_review(self):
        cases = [
            # Articles 111, 115, 137 : `class="lead mb-2"` / `class="small text-muted mb-2"`
            ('<p class="lead mb-2" style="opacity: 0.85;">Saison 11 · Article 1/5 · Gestion de Projet & Analytique CE</p>',
             'Gestion de Projet & Analytique CE'),
            ('<p class="lead mb-2" style="opacity: 0.85;">Saison 11 · Article 5/5 — Final · Gestion de Projet &amp; Analytique CE</p>',
             'Gestion de Projet &amp; Analytique CE'),
            ('<p class="small text-muted mb-2">Saison 12 — Administrer Odoo 19 CE · 7 / 7 · série complète</p>',
             'Administrer Odoo 19 CE'),
        ]
        for old, theme in cases:
            with self.subTest(old=old):
                opening = old[:old.index('>') + 1]
                self.assertEqual(markers.eyebrow_edits(BODY + old, 'Série'),
                                 [Edit('R1', old, opening + theme + '</p>', True)])
        # Prose (article 169) : pas un bandeau
        self.assertEqual(markers.eyebrow_edits("<p>L'article 2/3 démonte chaque clé.</p>", 'Série'), [])

    def test_unnumbered_eyebrow_is_left_alone(self):
        # Article 121, et les « Étape n » de l'article 95
        html = ('<p class="text-uppercase small mb-2 text-warning">Parcours Infrastructure · Série Tech-Email</p>'
                '<p class="text-uppercase small text-primary mb-2">Étape 1</p>')
        self.assertEqual(markers.eyebrow_edits(html, 'Infrastructure emailing'), [])


@tagged('post_install', '-at_install')
class TestMarkersNavigation(BaseCase):

    def test_navigation_only_sections_are_removed(self):
        for post_id, section in ((45, NAV_45), (61, NAV_61), (133, NAV_133), (111, NAV_111), (169, NAV_169)):
            with self.subTest(post=post_id):
                html = BODY + section + '\n'
                self.assertEqual(markers.nav_edits(html), [Edit('R2', section, '', False)])

    def test_navigation_with_a_link_outside_the_blog_is_reviewed(self):
        # Article 74 : le lien « suivant » mène au guide technique, pas à un article
        section = """<section class="s_text_block pt32 pb24">
    <div class="container">
        <div class="row">
            <div class="col-lg-10 mx-auto">
                <div class="d-flex justify-content-between align-items-center border-top pt-4">
                    <a href="/blog/developpement-odoo-2/actions-serveur-cron-et-automations-en-odoo-19-ircron-iractionsserver-et-baseautomation-73" class="btn btn-outline-secondary">
                        &larr; T22 — Actions serveur &amp; cron
                    </a>
                    <a href="/guide-technique-odoo" class="btn btn-warning">
                        Récupérer le guide technique complet &rarr;
                    </a>
                </div>
            </div>
        </div>
    </div>
</section>"""
        self.assertEqual(markers.nav_edits(BODY + section), [Edit('R2', section, '', True)])

    def test_navigation_next_to_guide_cta_removes_only_the_links(self):
        edits = markers.nav_edits(BODY + NAV_CTA_52)
        self.assertEqual(len(edits), 1)
        edit = edits[0]
        self.assertEqual((edit.rule, edit.new, edit.review), ('R2', '', True))
        self.assertTrue(edit.old.startswith('<div class="mt-4">'))
        self.assertTrue(edit.old.endswith('</div>'))
        self.assertIn('Installer avec Docker', edit.old)
        self.assertNotIn('Guide Technique', edit.old)
        new_html, statuses = markers.apply_edits(BODY + NAV_CTA_52, edits)
        self.assertEqual([s for _e, s in statuses], ['applied'])
        self.assertIn('Télécharger le guide', new_html)
        self.assertNotIn('Installer sur Ubuntu', new_html)
        self.assertEqual(new_html.count('<section'), new_html.count('</section>'))

    def test_next_article_with_summary_is_kept_and_its_title_cleaned(self):
        self.assertEqual(markers.nav_edits(BODY + NEXT_61), [])
        self.assertEqual(markers.nav_edits(BODY + NEXT_41), [])
        self.assertEqual(markers.tcode_label_edits(BODY + NEXT_61), [Edit(
            'R5', '<h2 class="text-white">Prochain article — T11</h2>',
            '<h2 class="text-white">Prochain article</h2>', False)])

    def test_sections_that_are_not_series_navigation_are_kept(self):
        self.assertEqual(markers.nav_edits(BODY + FORMATIONS_145), [])
        long_section = NAV_45.replace('</section>', '<p>%s</p></section>' % ('Un long paragraphe. ' * 25))
        self.assertEqual(markers.nav_edits(BODY + long_section), [])

    def test_restaurant_continuation_links_are_proposed_for_review(self):
        edits = markers.nav_edits(BODY + RESTAURANT_155)
        self.assertEqual(len(edits), 1)
        self.assertEqual((edits[0].rule, edits[0].new, edits[0].review), ('R2', '', True))
        self.assertTrue(edits[0].old.startswith('<div class="mt-4">'))
        self.assertNotIn('Continuer la Saison Restaurant', edits[0].old)


@tagged('post_install', '-at_install')
class TestMarkersSeriesBoxes(BaseCase):

    def test_see_also_in_this_series_is_removed(self):
        self.assertEqual(markers.see_also_series_edits(BODY + SEE_ALSO_65),
                         [Edit('R3', SEE_ALSO_65, '', False)])

    def test_series_list_alone_removes_the_section(self):
        # Article 172 sans sa phrase finale : titre + liste seulement
        alone = SERIES_172.replace(SERIES_172[SERIES_172.index('                <p>'):SERIES_172.index('            </div>')], '')
        self.assertNotIn('Chaque article', alone)
        self.assertEqual(markers.series_list_edits(BODY + alone), [Edit('R4', alone, '', False)])

    def test_series_list_keeps_the_explanatory_sentence(self):
        # Article 172 : la phrase « Chaque article reprend… » n'est pas un repère
        html = BODY + SERIES_172
        edits = markers.series_list_edits(html)
        self.assertEqual(len(edits), 1)
        self.assertEqual((edits[0].new, edits[0].review), ('', True))
        self.assertTrue(edits[0].old.startswith('<h3>La série'))
        self.assertTrue(edits[0].old.endswith('</ul>'))
        new_html, statuses = markers.apply_edits(html, edits)
        self.assertEqual([s for _e, s in statuses], ['applied'])
        self.assertIn('Chaque article reprend la base du précédent', new_html)

    def test_series_list_with_trailing_navigation_is_reviewed(self):
        # Article 173 : « Article 2/5 — précédent : … Suivant : … » après la liste
        html = BODY + SERIES_173
        edits = markers.series_list_edits(html)
        self.assertEqual(len(edits), 1)
        self.assertEqual((edits[0].new, edits[0].review), ('', True))
        self.assertNotIn('Suivant', edits[0].old)
        new_html, _statuses = markers.apply_edits(html, edits)
        self.assertIn('Charger son stock initial dans Odoo 19 Community', new_html)

    def test_series_card_grid_is_always_reviewed(self):
        # Article 171 : la grille mêle une carte hors série (« Architecture technique Odoo 19 »)
        edits = markers.series_list_edits(BODY + SERIES_171)
        self.assertEqual(edits, [Edit('R4', SERIES_171, '', True)])
        # Et si la section contient autre chose que la grille, seuls le titre et la grille partent
        mixed = SERIES_171.replace('        </div>\n    </div>\n</section>',
                                   '        </div>\n    <p>Voir aussi le <a href="/blog/developpement-odoo-2">blog</a>.</p></div>\n</section>')
        edits = markers.series_list_edits(BODY + mixed)
        self.assertEqual(len(edits), 1)
        self.assertTrue(edits[0].review)
        self.assertTrue(edits[0].old.startswith('<h3 class="text-center mb-4">La série'))
        self.assertNotIn('Voir aussi le', edits[0].old)

    def test_series_list_with_other_content_removes_only_title_and_list(self):
        html = BODY + SERIES_165
        self.assertEqual(markers.series_list_edits(html), [Edit('R4', SERIES_165_LIST, '', True)])
        new_html, _statuses = markers.apply_edits(html, markers.series_list_edits(html))
        self.assertIn('Côté fonctionnel, sans écrire de code', new_html)
        self.assertNotIn('La série Traduction', new_html)
        self.assertEqual(new_html.count('<section'), 2)


@tagged('post_install', '-at_install')
class TestMarkersTCodes(BaseCase):

    def test_tcode_prefix_and_suffix_removed_from_labels(self):
        html = BODY + '<p>Avoir lu %s</p>\n<h2 class="text-white">Prochain article — T23 · fin du Bloc 5</h2>' % LINK_T09_61
        self.assertEqual(markers.tcode_label_edits(html), [
            Edit('R5', LINK_T09_61, LINK_T09_61.replace('T09 — ', ''), False),
            Edit('R5', '<h2 class="text-white">Prochain article — T23 · fin du Bloc 5</h2>',
                 '<h2 class="text-white">Prochain article</h2>', False),
        ])

    def test_bare_tcode_link_is_left_for_review(self):
        html = BODY + '<p>Voir %s pour les relations.</p>' % LINK_T11_65
        self.assertEqual(markers.tcode_label_edits(html), [Edit('R5', LINK_T11_65, LINK_T11_65, True)])

    def test_tcode_in_code_and_comments_is_untouched(self):
        html = PRE_61 + '\n<!-- T10 : repère interne -->\n<p>Avoir lu %s</p>' % LINK_T09_61
        spans = markers.protected_spans(html)
        self.assertIn((0, len(PRE_61)), spans)
        comment = '<!-- T10 : repère interne -->'
        self.assertIn((html.index(comment), html.index(comment) + len(comment)), spans)
        edits = markers.tcode_label_edits(html)
        self.assertEqual([e.old for e in edits], [LINK_T09_61])
        new_html, _statuses = markers.apply_edits(html, edits)
        self.assertTrue(new_html.startswith(PRE_61))
        self.assertIn(comment, new_html)
        self.assertEqual(markers.residual_markers(new_html), [])

    def test_residual_markers_outside_code(self):
        html = PRE_61 + '<p>Voir l\'article T24 et la Suite de la Saison 2.</p><p>Article 3/5</p>'
        found = markers.residual_markers(html)
        self.assertEqual(len(found), 3)
        self.assertTrue(all(len(excerpt) <= 120 for excerpt in found))
        self.assertTrue(all('Champs non-relationnels' not in excerpt for excerpt in found))


@tagged('post_install', '-at_install')
class TestMarkersApply(BaseCase):

    HTML = '<p>Un</p><p class="x">Bloc 1 · Installation — Article 1/3</p><p>Deux</p>'
    OLD = '<p class="x">Bloc 1 · Installation — Article 1/3</p>'
    NEW = '<p class="x">Installation</p>'

    def test_applied_then_already(self):
        edit = Edit('R1', self.OLD, self.NEW, False)
        new_html, statuses = markers.apply_edits(self.HTML, [edit])
        self.assertEqual(new_html, '<p>Un</p><p class="x">Installation</p><p>Deux</p>')
        self.assertEqual(statuses, [(edit, 'applied')])
        again, statuses = markers.apply_edits(new_html, [edit])
        self.assertEqual(again, new_html)
        self.assertEqual(statuses, [(edit, 'already')])

    def test_missing_leaves_html_unchanged(self):
        good = Edit('R1', self.OLD, self.NEW, False)
        absent = Edit('R2', '<section>absente</section>', '<section>autre</section>', False)
        new_html, statuses = markers.apply_edits(self.HTML, [good, absent])
        self.assertEqual(new_html, self.HTML)
        self.assertEqual([s for _e, s in statuses], ['applied', 'missing'])

    def test_absent_deletion_is_missing_not_already(self):
        good = Edit('R1', self.OLD, self.NEW, False)
        gone = Edit('R2', '<section class="s_text_block">jamais présente</section>', '', False)
        new_html, statuses = markers.apply_edits(self.HTML, [good, gone])
        self.assertEqual(new_html, self.HTML)
        self.assertEqual([s for _e, s in statuses], ['applied', 'missing'])
        # Même une suppression réellement déjà faite reste « missing » (non distinguable)
        _html, statuses = markers.apply_edits('<p>Deux</p>', [Edit('R3', '<p>Un</p>', '', False)])
        self.assertEqual([s for _e, s in statuses], ['missing'])

    def test_replacement_already_done_is_already(self):
        edit = Edit('R5', '<h2>Prochain article — T11</h2>', '<h2>Prochain article</h2>', False)
        html = '<section><h2>Prochain article</h2><p>Résumé.</p></section>'
        new_html, statuses = markers.apply_edits(html, [edit])
        self.assertEqual((new_html, statuses), (html, [(edit, 'already')]))

    def test_ambiguous_leaves_html_unchanged(self):
        good = Edit('R1', self.OLD, self.NEW, False)
        twice = Edit('R5', '<p>', '<p class="y">', False)
        new_html, statuses = markers.apply_edits(self.HTML, [good, twice])
        self.assertEqual(new_html, self.HTML)
        self.assertEqual([s for _e, s in statuses], ['applied', 'ambiguous'])


@tagged('post_install', '-at_install')
class TestMarkersPropose(BaseCase):

    def test_propose_drops_edits_inside_a_removed_section(self):
        html = EYEBROW_169 + BODY + NAV_169
        edits = markers.propose(html, 'Licences et distribution', True)
        self.assertEqual(edits, [
            Edit('R1', EYEBROW_169, '<p class="text-uppercase small mb-2 text-warning">Licences et distribution</p>', False),
            Edit('R2', NAV_169, '', False),
        ])
        new_html, statuses = markers.apply_edits(html, edits)
        self.assertEqual({s for _e, s in statuses}, {'applied'})
        self.assertEqual(markers.residual_markers(new_html), [])

    def test_propose_without_series_keeps_navigation(self):
        edits = markers.propose(BODY + NAV_61, False, False)
        self.assertEqual([e.rule for e in edits], ['R5', 'R5'])
        self.assertNotIn('R2', {e.rule for e in edits})

    def test_propose_makes_repeated_labels_unique(self):
        # Article 66 : deux liens « T12 » identiques dans la prose
        link = '<a href="/blog/developpement-odoo-2/contraintes-et-champs-calcules-odoo-19-apidepends-modelsconstraint-63">T12</a>'
        html = '<p>Les computes de %s restent valables.</p>\n<p>Les contraintes de %s aussi.</p>' % (link, link)
        edits = markers.propose(html, 'Parcours', True)
        self.assertEqual(len(edits), 2)
        self.assertTrue(all(html.count(e.old) == 1 and e.review for e in edits))
        self.assertTrue(all(len(e.old) <= len(link) + 16 for e in edits))  # élargi d'un seul côté
        _new, statuses = markers.apply_edits(html, edits)
        self.assertEqual({s for _e, s in statuses}, {'applied'})

    def test_widening_never_crosses_protected_code(self):
        link = LINK_T09_61
        # Unicité atteignable côté texte : l'élargissement s'arrête avant le <code>
        html = ('<p>Voir %s<code>_order</code> ici.</p>\n<p>Relire %s<code>_order</code> ici.</p>' % (link, link))
        edits = markers.propose(html, 'Parcours', True)
        self.assertEqual(len(edits), 2)
        for edit in edits:
            self.assertEqual(html.count(edit.old), 1)
            self.assertNotIn('<code>', edit.old)
            self.assertFalse(edit.review)
        new_html, statuses = markers.apply_edits(html, edits)
        self.assertEqual({s for _e, s in statuses}, {'applied'})
        self.assertEqual(new_html.count('<code>_order</code>'), 2)
        # Unicité impossible sans franchir un <code> : `old` étroit, à relire, et l'application refuse
        html = '<p><code>a</code>%s<code>b</code></p>\n<p><code>a</code>%s<code>b</code></p>' % (link, link)
        edits = markers.propose(html, 'Parcours', True)
        self.assertEqual([(e.old, e.review) for e in edits], [(link, True), (link, True)])
        new_html, statuses = markers.apply_edits(html, edits)
        self.assertEqual(new_html, html)
        self.assertIn('ambiguous', {s for _e, s in statuses})


@tagged('post_install', '-at_install')
class TestMarkersResidueAndPlan(BaseCase):

    def test_residual_markers_see_article_number_after_any_blank(self):
        # Article 176 : « Article&nbsp;5/5 » ; article 171 : « l'article » + saut de ligne + « 1/3 »
        cases = [
            '<p class="mb-0"><strong>Article&nbsp;5/5</strong> — précédent&nbsp;: …</p>',
            "<p>ce que l'article\n                1/3 appelait « l'illusion de la protection ».</p>",
            '<p>Article&#160;2/3</p>',
            '<p>Article\u00a04/5</p>',
        ]
        for html in cases:
            with self.subTest(html=html):
                self.assertEqual(len(markers.residual_markers(html)), 1)
        self.assertEqual(markers.residual_markers('<code>Article&nbsp;5/5</code>'), [])

    def test_build_post_plan_drops_skips_placeholders_and_appends_curated(self):
        html = BODY + '<p>Voir %s pour les relations.</p>' % LINK_T11_65 + NAV_61
        proposed = markers.propose(html, 'Parcours', True)
        self.assertIn(Edit('R5', LINK_T11_65, LINK_T11_65, True), proposed)
        curated = [('Voir %s pour' % LINK_T11_65, 'Voir <a href="/x-62">Relations entre modèles</a> pour', 'R5 — lien complété'),
                   ("Contenu de l'article.", 'Contenu.', 'reformulation')]
        plan = markers.build_post_plan(html, 'Parcours', True, curated=curated, drop=['T11 — Relations entre modèles'])
        self.assertNotIn(LINK_T11_65, [e.old for e in plan])        # lien « T11 » seul : jamais gardé tel quel
        self.assertNotIn('R2', [e.rule for e in plan])              # navigation écartée par l'extrait
        self.assertEqual(plan[-2:], [
            Edit('R5', curated[0][0], curated[0][1], False),
            Edit('M', curated[1][0], curated[1][1], False),
        ])
        new_html, statuses = markers.apply_edits(html, plan)
        self.assertEqual({s for _e, s in statuses}, {'applied'})
        self.assertIn('Relations entre modèles</a> pour', new_html)


class _TagBalance(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.balance = {'section': 0, 'div': 0}

    def handle_starttag(self, tag, attrs):
        if tag in self.balance:
            self.balance[tag] += 1

    def handle_endtag(self, tag):
        if tag in self.balance:
            self.balance[tag] -= 1


def _balance(html):
    parser = _TagBalance()
    parser.feed(html)
    parser.close()
    return parser.balance


@tagged('post_install', '-at_install')
class TestMarkersSnapshot(BaseCase):
    """Relecture complète sur l'instantané de production (non versionné) :
    OSKI_MARKERS_SNAPSHOT=<chemin de prod_posts.json>, prod_series.json dans le même dossier."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        path = os.environ.get('OSKI_MARKERS_SNAPSHOT')
        cls.posts = cls.series = None
        if path and os.path.exists(path):
            with open(path, encoding='utf-8') as handle:
                cls.posts = json.load(handle)
            with open(os.path.join(os.path.dirname(path), 'prod_series.json'), encoding='utf-8') as handle:
                cls.series = json.load(handle)

    def setUp(self):
        super().setUp()
        if self.posts is None:
            self.skipTest('OSKI_MARKERS_SNAPSHOT absent : instantané de production non disponible')

    def _plan(self, post):
        name = self.series[str(post['series'])]['name'] if post['series'] else False
        return markers.build_post_plan(post['content'], name, bool(post['series']),
                                       markers_curated.CURATED.get(post['id'], ()),
                                       markers_curated.DROP.get(post['id'], ()))

    def test_curated_and_drop_entries_are_unique_in_the_snapshot(self):
        by_id = {post['id']: post for post in self.posts}
        for table in (markers_curated.CURATED, markers_curated.DROP):
            for post_id, entries in table.items():
                self.assertIn(post_id, by_id)
                content = by_id[post_id]['content']
                for entry in entries:
                    old = entry[0] if isinstance(entry, tuple) else entry
                    with self.subTest(post=post_id, old=old[:80]):
                        self.assertEqual(content.count(old), 1)

    def test_each_drop_entry_matches_exactly_one_proposal(self):
        by_id = {post['id']: post for post in self.posts}
        for post_id, extracts in markers_curated.DROP.items():
            post = by_id[post_id]
            name = self.series[str(post['series'])]['name'] if post['series'] else False
            proposals = markers.propose(post['content'], name, bool(post['series']))
            for extract in extracts:
                with self.subTest(post=post_id, extract=extract[:80]):
                    self.assertEqual(sum(extract in edit.old for edit in proposals), 1)

    def test_plan_applies_everywhere_and_leaves_only_accepted_residue(self):
        for post in self.posts:
            with self.subTest(post=post['id']):
                new_html, statuses = markers.apply_edits(post['content'], self._plan(post))
                self.assertFalse([s for _e, s in statuses if s in ('missing', 'ambiguous')])
                accepted = markers_curated.ACCEPTED_RESIDUE.get(post['id'], [])
                residue = markers.residual_markers(new_html)
                self.assertLessEqual(set(residue), set(accepted))
                self.assertLessEqual(set(accepted), set(residue))  # pas d'entrée périmée

    def test_plan_keeps_section_and_div_balance(self):
        for post in self.posts:
            with self.subTest(post=post['id']):
                new_html, _statuses = markers.apply_edits(post['content'], self._plan(post))
                self.assertEqual(_balance(new_html), _balance(post['content']))
                removed = sum(edit.old.count('<section') - edit.new.count('<section') for edit in self._plan(post))
                self.assertEqual(len(re.findall(r'<section\b', new_html)),
                                 len(re.findall(r'<section\b', post['content'])) - removed)


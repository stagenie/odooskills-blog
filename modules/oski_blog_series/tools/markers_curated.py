"""Relecture des repères de série : remplacements exacts, propositions écartées, résidus admis.

Données pures (aucun import), consommées par `markers.build_post_plan` et l'application (tâche 4).
- CURATED[post_id] = [(old, new, note)] : `old` présent une seule fois dans l'article ; la note
  commence par la règle (« R5 — … ») ; `new == ''` = suppression.
- DROP[post_id] = [extrait] : extrait unique qui identifie une proposition de `markers.propose`
  à ne pas appliquer (la raison est en commentaire).
- ACCEPTED_RESIDUE[post_id] = [extrait de `residual_markers`] : résidus volontairement gardés."""

# Table T → article vérifiée sur l'instantané (noms, positions dans la série « Parcours
# Fondamentaux du développeur » puis « Aller plus loin en v19 ») :
#   T01 50 Installer Odoo 19 sur Ubuntu        T15 66 Méthodes de modèle
#   T02 52 Installer Odoo 19 sur Windows       T16 67 Vues Form, List et Search
#   T03 53 Installer Odoo 19 avec Docker       T17 68 Vues Kanban, Graph et Pivot
#   T04 54 Configurer l'environnement de dév.  T18 69 Héritage de vues
#   T05 55 Première approche du développement  T19 70 Wizards et assistants
#   T06 56 Architecture technique              T20 71 Rapports QWeb PDF
#   T07 57 Gestion des bases de données        T21 72 Email templates et mail.thread
#   T08 59 Modèles de base                     T22 73 Actions serveur, cron et automations
#   T09 60 Attributs de modèles                T23 74 Controllers HTTP et API REST
#   T10 61 Champs non-relationnels             T24 105 Tests automatisés
#   T11 62 Relations entre modèles             T25 106 Migration Odoo 18 → 19
#   T12 63 Contraintes et champs calculés      T26 107 OWL composants custom
#   T13 64 Héritage des modèles                T27 108 bus.bus + WebSocket
#   T14 65 Hiérarchie de modèles               T28 109 Mesurer la performance de bus.bus
# Ancres fausses rencontrées : « T01 » → …-56 (Architecture technique) et « T15 » → …-65
# (Hiérarchie) dans 105–109 ; les remplacements pointent vers 50 et 66.

CURATED = {
    # 41 — Les unités de mesure et conditionnements dans Odoo 19
    41: [
        ('<p><a href="/blog/fonctionnel-odoo-1/configurer-linventaire-dans-odoo-19-entrepot-produits-et-stock-initial-40" class="text-white-75">← Article précédent : Configurer l\'inventaire</a></p>',
         '',
         'R2 — lien « ← Article précédent » intra-série retiré ; le bloc « Prochain article » et son résumé restent'),
    ],
    # 54 — Configurer l'environnement de développement Odoo 19
    54: [
        ('(article T01 ou T02 de cette série)',
         '(voir <a href="/blog/developpement-odoo-2/installer-odoo-19-sur-ubuntu-2404-lts-50">Installer Odoo 19 sur Ubuntu</a> ou <a href="/blog/developpement-odoo-2/installer-odoo-19-sur-windows-1011-52">sur Windows</a>)',
         "R5 — code T remplacé par un lien vers l'article visé"),
    ],
    # 55 — Première approche du développement Odoo 19
    55: [
        ('(article T01, T02 ou T03)',
         '(voir <a href="/blog/developpement-odoo-2/installer-odoo-19-sur-ubuntu-2404-lts-50">Installer Odoo 19 sur Ubuntu</a>, <a href="/blog/developpement-odoo-2/installer-odoo-19-sur-windows-1011-52">sur Windows</a> ou <a href="/blog/developpement-odoo-2/installer-odoo-19-avec-docker-53">avec Docker</a>)',
         "R5 — code T remplacé par un lien vers l'article visé"),
        ('(article T04)',
         '(voir <a href="/blog/developpement-odoo-2/configurer-lenvironnement-de-developpement-odoo-19-54">Configurer l\'environnement de développement</a>)',
         "R5 — code T remplacé par un lien vers l'article visé"),
    ],
    # 56 — Architecture technique Odoo 19
    56: [
        ("Avoir lu l'article T05 (première approche du développement)",
         'Avoir lu l\'article <a href="/blog/developpement-odoo-2/premiere-approche-du-developpement-odoo-19-55">Première approche du développement</a>',
         "R5 — code T remplacé par un lien vers l'article visé"),
        ('(T01, T02 ou T03)',
         '(voir <a href="/blog/developpement-odoo-2/installer-odoo-19-sur-ubuntu-2404-lts-50">Installer Odoo 19 sur Ubuntu</a>, <a href="/blog/developpement-odoo-2/installer-odoo-19-sur-windows-1011-52">sur Windows</a> ou <a href="/blog/developpement-odoo-2/installer-odoo-19-avec-docker-53">avec Docker</a>)',
         "R5 — code T remplacé par un lien vers l'article visé"),
        ('Un IDE configuré (T04)',
         'Un IDE configuré (voir <a href="/blog/developpement-odoo-2/configurer-lenvironnement-de-developpement-odoo-19-54">Configurer l\'environnement de développement</a>)',
         "R5 — code T remplacé par un lien vers l'article visé"),
        ('des champs (T10),',
         'des champs,',
         'R5 — code T retiré (renvoi vers « les articles suivants »)'),
        ("des relations (T11), des contraintes (T12), de l'héritage (T13) et des vues (T16)",
         "des relations, des contraintes, de l'héritage et des vues",
         'R5 — codes T retirés (renvoi vers « les articles suivants »)'),
        ("dans l'article T16.",
         'dans l\'article <a href="/blog/developpement-odoo-2/vues-form-list-et-search-en-odoo-19-actions-menus-et-widgets-67">Vues Form, List et Search</a>.',
         "R5 — code T remplacé par un lien vers l'article visé"),
    ],
    # 57 — Gestion des bases de données Odoo 19
    57: [
        ('(T01, T02 ou T03)',
         '(voir <a href="/blog/developpement-odoo-2/installer-odoo-19-sur-ubuntu-2404-lts-50">Installer Odoo 19 sur Ubuntu</a>, <a href="/blog/developpement-odoo-2/installer-odoo-19-sur-windows-1011-52">sur Windows</a> ou <a href="/blog/developpement-odoo-2/installer-odoo-19-avec-docker-53">avec Docker</a>)',
         "R5 — code T remplacé par un lien vers l'article visé"),
        ('(article T20 de cette série)',
         '(voir <a href="/blog/developpement-odoo-2/actions-serveur-cron-et-automations-en-odoo-19-ircron-iractionsserver-et-baseautomation-73">Actions serveur, cron et automations</a>)',
         "R5 — code T remplacé par un lien vers l'article visé ; « T20 » visait les rapports PDF, le cron est traité dans « Actions serveur, cron et automations »"),
    ],
    # 59 — Modèles de base Odoo 19 : Model, TransientModel, AbstractModel
    59: [
        ('Avoir lu les articles T05 (première approche) et T06 (architecture)',
         'Avoir lu les articles <a href="/blog/developpement-odoo-2/premiere-approche-du-developpement-odoo-19-55">Première approche du développement</a> et <a href="/blog/developpement-odoo-2/architecture-technique-odoo-19-56">Architecture technique</a>',
         "R5 — code T remplacé par un lien vers l'article visé"),
        ('<text x="60" y="382" font-size="13" font-weight="bold" fill="#333">Exemple T08</text>',
         '<text x="60" y="382" font-size="13" font-weight="bold" fill="#333">Exemple</text>',
         'R5 — code T (article courant) retiré du schéma'),
        ('<text x="340" y="382" font-size="13" font-weight="bold" fill="#333">Exemple T08</text>',
         '<text x="340" y="382" font-size="13" font-weight="bold" fill="#333">Exemple</text>',
         'R5 — code T (article courant) retiré du schéma'),
        ('<text x="620" y="382" font-size="13" font-weight="bold" fill="#333">Exemple T08</text>',
         '<text x="620" y="382" font-size="13" font-weight="bold" fill="#333">Exemple</text>',
         'R5 — code T (article courant) retiré du schéma'),
        ('<strong>Article suivant (T09)</strong>',
         '<strong>Article suivant</strong>',
         "R5 — code T retiré (doublon d'un lien voisin ou article courant)"),
    ],
    # 60 — Attributs de modèles Odoo 19 : _order, _rec_name, Constraint
    60: [
        ("l'article T12 (champs calculés)",
         'l\'article <a href="/blog/developpement-odoo-2/contraintes-et-champs-calcules-odoo-19-apidepends-modelsconstraint-63">Contraintes et champs calculés</a>',
         "R5 — code T remplacé par un lien vers l'article visé"),
        ("sans l'expliquer dans T08.",
         'sans l\'expliquer dans <a href="/blog/developpement-odoo-2/modeles-de-base-odoo-19-model-transientmodel-abstractmodel-59">Modèles de base</a>.',
         "R5 — code T remplacé par un lien vers l'article visé"),
        ("L'article T13 couvrira",
         'L\'article <a href="/blog/developpement-odoo-2/heritage-des-modeles-odoo-19-inherit-inherits-abstractmodel-64">Héritage des modèles</a> couvrira',
         "R5 — code T remplacé par un lien vers l'article visé"),
        ("l'article T14 (hiérarchie)",
         'l\'article <a href="/blog/developpement-odoo-2/hierarchie-de-modeles-odoo-19-parent-id-child-ids-parent-store-65">Hiérarchie de modèles</a>',
         "R5 — code T remplacé par un lien vers l'article visé"),
        ('<strong>Article suivant (T10)</strong>',
         '<strong>Article suivant</strong>',
         "R5 — code T retiré (doublon d'un lien voisin ou article courant)"),
        ('<strong>Article T12</strong>',
         '<strong><a href="/blog/developpement-odoo-2/contraintes-et-champs-calcules-odoo-19-apidepends-modelsconstraint-63">Contraintes et champs calculés</a></strong>',
         "R5 — code T remplacé par un lien vers l'article visé"),
    ],
    # 61 — Champs non-relationnels Odoo 19 : Char, Float, Date, Html, Monetary…
    61: [
        ('complet après T10, version',
         'complet, version',
         "R5 — code T retiré (doublon d'un lien voisin ou article courant)"),
    ],
    # 62 — Relations entre modèles Odoo 19 : Many2one, One2many, Many2many
    62: [
        ('ajoutés à T11 :',
         'ajoutés dans cet article :',
         "R5 — code T de l'article courant reformulé"),
    ],
    # 63 — Contraintes et champs calculés Odoo 19 : @api.depends, models.Constraint
    63: [
        ('Odoo 19</a> (T10)',
         'Odoo 19</a>',
         "R5 — code T retiré (doublon d'un lien voisin ou article courant)"),
        ('ajouts T12 dans',
         'ajouts dans',
         "R5 — code T retiré (doublon d'un lien voisin ou article courant)"),
    ],
    # 64 — Héritage des modèles Odoo 19 : _inherit, _inherits, AbstractModel
    64: [
        ('AbstractModel</a> (T08)',
         'AbstractModel</a>',
         "R5 — code T retiré (doublon d'un lien voisin ou article courant)"),
        ('>Exemple T13</text>',
         '>Exemple</text>',
         'R5 — code T (article courant) retiré du schéma'),
        ('Récapitulatif — fichiers T13',
         "Récapitulatif — fichiers de l'article",
         "R5 — code T de l'article courant reformulé"),
    ],
    # 65 — Hiérarchie de modèles Odoo 19 : parent_id, child_ids, _parent_store
    65: [
        ('de <a href="/blog/developpement-odoo-2/heritage-des-modeles-odoo-19-inherit-inherits-abstractmodel-64">T13</a> installé',
         'de l\'article <a href="/blog/developpement-odoo-2/heritage-des-modeles-odoo-19-inherit-inherits-abstractmodel-64">Héritage des modèles</a> installé',
         "R5 — code T remplacé par le titre de l'article visé"),
        ('(voir <a href="/blog/developpement-odoo-2/relations-entre-modeles-odoo-19-many2one-one2many-many2many-62">T11</a>)',
         '(voir <a href="/blog/developpement-odoo-2/relations-entre-modeles-odoo-19-many2one-one2many-many2many-62">Relations entre modèles</a>)',
         "R5 — code T remplacé par le titre de l'article visé"),
        ('(voir <a href="/blog/developpement-odoo-2/contraintes-et-champs-calcules-odoo-19-apidepends-modelsconstraint-63">T12</a>)',
         '(voir <a href="/blog/developpement-odoo-2/contraintes-et-champs-calcules-odoo-19-apidepends-modelsconstraint-63">Contraintes et champs calculés</a>)',
         "R5 — code T remplacé par le titre de l'article visé"),
        ("Jusqu'à T13, une",
         "Jusqu'ici, une",
         'R5 — code T reformulé'),
        ('En T12, on avait posé',
         'Dans <a href="/blog/developpement-odoo-2/contraintes-et-champs-calcules-odoo-19-apidepends-modelsconstraint-63">Contraintes et champs calculés</a>, on avait posé',
         "R5 — code T remplacé par un lien vers l'article visé"),
        ('fichier complet T14</h2>',
         'fichier complet</h2>',
         "R5 — code T retiré (doublon d'un lien voisin ou article courant)"),
    ],
    # 66 — Méthodes de modèle Odoo 19 : create, write, unlink et @api.model_create_multi
    66: [
        ('de <a href="/blog/developpement-odoo-2/hierarchie-de-modeles-odoo-19-parent-id-child-ids-parent-store-65">T14</a> installé',
         'de l\'article <a href="/blog/developpement-odoo-2/hierarchie-de-modeles-odoo-19-parent-id-child-ids-parent-store-65">Hiérarchie de modèles</a> installé',
         "R5 — code T remplacé par le titre de l'article visé"),
        ('modèles (<a href="/blog/developpement-odoo-2/modeles-de-base-odoo-19-model-transientmodel-abstractmodel-59">T08</a>), champs (<a href="/blog/developpement-odoo-2/champs-non-relationnels-odoo-19-char-float-date-html-monetary-61">T10</a>), contraintes (<a href="/blog/developpement-odoo-2/contraintes-et-champs-calcules-odoo-19-apidepends-modelsconstraint-63">T12</a>)',
         'modèles (<a href="/blog/developpement-odoo-2/modeles-de-base-odoo-19-model-transientmodel-abstractmodel-59">Modèles de base</a>), champs (<a href="/blog/developpement-odoo-2/champs-non-relationnels-odoo-19-char-float-date-html-monetary-61">Champs non-relationnels</a>), contraintes (<a href="/blog/developpement-odoo-2/contraintes-et-champs-calcules-odoo-19-apidepends-modelsconstraint-63">Contraintes et champs calculés</a>)',
         "R5 — code T remplacé par le titre de l'article visé"),
        ('(voir <a href="/blog/developpement-odoo-2/contraintes-et-champs-calcules-odoo-19-apidepends-modelsconstraint-63">T12</a>).</td>',
         '(voir <a href="/blog/developpement-odoo-2/contraintes-et-champs-calcules-odoo-19-apidepends-modelsconstraint-63">Contraintes et champs calculés</a>).</td>',
         "R5 — code T remplacé par le titre de l'article visé"),
    ],
    # 67 — Vues Form, List et Search en Odoo 19 : actions, menus et widgets
    67: [
        ('(<a href="/blog/developpement-odoo-2/methodes-de-modele-odoo-19-create-write-unlink-et-apimodel-create-multi-66">T15</a>).</li>',
         '(<a href="/blog/developpement-odoo-2/methodes-de-modele-odoo-19-create-write-unlink-et-apimodel-create-multi-66">Méthodes de modèle</a>).</li>',
         "R5 — code T remplacé par le titre de l'article visé"),
        ('du modèle (T10/T11).',
         'du modèle (voir <a href="/blog/developpement-odoo-2/champs-non-relationnels-odoo-19-char-float-date-html-monetary-61">Champs non-relationnels</a> et <a href="/blog/developpement-odoo-2/relations-entre-modeles-odoo-19-many2one-one2many-many2many-62">Relations entre modèles</a>).',
         "R5 — code T remplacé par un lien vers l'article visé"),
        ('<code>create()</code> (T15).</figcaption>',
         '<code>create()</code> (voir <a href="/blog/developpement-odoo-2/methodes-de-modele-odoo-19-create-write-unlink-et-apimodel-create-multi-66">Méthodes de modèle</a>).</figcaption>',
         "R5 — code T remplacé par un lien vers l'article visé"),
        ('<code>action_resolve</code> de T15).',
         '<code>action_resolve</code> de <a href="/blog/developpement-odoo-2/methodes-de-modele-odoo-19-create-write-unlink-et-apimodel-create-multi-66">Méthodes de modèle</a>).',
         "R5 — code T remplacé par un lien vers l'article visé"),
        ('du T14 affiche',
         'vue dans <a href="/blog/developpement-odoo-2/hierarchie-de-modeles-odoo-19-parent-id-child-ids-parent-store-65">Hiérarchie de modèles</a> affiche',
         "R5 — code T remplacé par un lien vers l'article visé"),
    ],
    # 68 — Vues Kanban, Graph et Pivot en Odoo 19 : QWeb, widgets et dashboards
    68: [
        ('(<a href="/blog/developpement-odoo-2/vues-form-list-et-search-en-odoo-19-actions-menus-et-widgets-67">T16</a>).',
         '(<a href="/blog/developpement-odoo-2/vues-form-list-et-search-en-odoo-19-actions-menus-et-widgets-67">Vues Form, List et Search</a>).',
         "R5 — code T remplacé par le titre de l'article visé"),
    ],
    # 69 — Héritage de vues en Odoo 19 : xpath, inherit_id et les 5 positions
    69: [
        ('(<a href="/blog/developpement-odoo-2/vues-kanban-graph-et-pivot-en-odoo-19-qweb-widgets-et-dashboards-68">T17</a>).',
         '(<a href="/blog/developpement-odoo-2/vues-kanban-graph-et-pivot-en-odoo-19-qweb-widgets-et-dashboards-68">Vues Kanban, Graph et Pivot</a>).',
         "R5 — code T remplacé par le titre de l'article visé"),
        ('dès <a href="/blog/developpement-odoo-2/heritage-des-modeles-odoo-19-inherit-inherits-abstractmodel-64">T13</a>.',
         'dès <a href="/blog/developpement-odoo-2/heritage-des-modeles-odoo-19-inherit-inherits-abstractmodel-64">Héritage des modèles</a>.',
         "R5 — code T remplacé par le titre de l'article visé"),
        (('SARL</em> en\n'
          '                    <a href="/blog/developpement-odoo-2/vues-form-list-et-search-en-odoo-19-actions-menus-et-widgets-67">T16</a>)'),
         ('SARL</em> dans\n'
          '                    l\'article <a href="/blog/developpement-odoo-2/vues-form-list-et-search-en-odoo-19-actions-menus-et-widgets-67">Vues Form, List et Search</a>)'),
         "R5 — code T remplacé par le titre de l'article visé"),
    ],
    # 70 — Wizards et assistants en Odoo 19 : TransientModel, target='new' et binding_model
    70: [
        ('(<a href="/blog/developpement-odoo-2/heritage-de-vues-en-odoo-19-xpath-inherit-id-et-les-5-positions-69">T18</a>).',
         '(<a href="/blog/developpement-odoo-2/heritage-de-vues-en-odoo-19-xpath-inherit-id-et-les-5-positions-69">Héritage de vues</a>).',
         "R5 — code T remplacé par le titre de l'article visé"),
        ("Maîtrise des vues form (T16) et de l'héritage de vues (T18).",
         "Maîtrise des vues form et de l'héritage de vues.",
         "R5 — code T retiré (doublon d'un lien voisin ou article courant)"),
        ('Avec ce T19, la <strong>série UI (Bloc 4)</strong> est complète.',
         'Avec cet article, la <strong>série UI</strong> est complète.',
         'R6 — numérotation narrative (code T, n° de bloc) reformulée'),
        ('<strong>T19 — Wizards (cet article)</strong>',
         '<strong>Wizards (cet article)</strong>',
         "R5 — code T retiré (doublon d'un lien voisin ou article courant)"),
        ('démarre au T20.',
         'démarre avec <a href="/blog/developpement-odoo-2/rapports-qweb-pdf-en-odoo-19-iractionsreport-external-layout-et-wkhtmltopdf-71">Rapports QWeb PDF</a>.',
         "R5 — code T remplacé par un lien vers l'article visé"),
    ],
    # 71 — Rapports QWeb PDF en Odoo 19 : ir.actions.report, external_layout et wkhtmltopdf
    71: [
        ('(<a href="/blog/developpement-odoo-2/wizards-et-assistants-en-odoo-19-transientmodel-targetnew-et-binding-model-id-70">T19</a>).',
         '(<a href="/blog/developpement-odoo-2/wizards-et-assistants-en-odoo-19-transientmodel-targetnew-et-binding-model-id-70">Wizards et assistants</a>).',
         "R5 — code T remplacé par le titre de l'article visé"),
        ('(<a href="/blog/developpement-odoo-2/vues-kanban-graph-et-pivot-en-odoo-19-qweb-widgets-et-dashboards-68">T17</a>) et',
         '(<a href="/blog/developpement-odoo-2/vues-kanban-graph-et-pivot-en-odoo-19-qweb-widgets-et-dashboards-68">Vues Kanban, Graph et Pivot</a>) et',
         "R5 — code T remplacé par le titre de l'article visé"),
        ('(<a href="/blog/developpement-odoo-2/heritage-de-vues-en-odoo-19-xpath-inherit-id-et-les-5-positions-69">T18</a>).',
         '(<a href="/blog/developpement-odoo-2/heritage-de-vues-en-odoo-19-xpath-inherit-id-et-les-5-positions-69">Héritage de vues</a>).',
         "R5 — code T remplacé par le titre de l'article visé"),
    ],
    # 72 — Email templates et mail.thread en Odoo 19 : envoi automatique depuis create et w
    72: [
        ('(<a href="/blog/developpement-odoo-2/rapports-qweb-pdf-en-odoo-19-iractionsreport-external-layout-et-wkhtmltopdf-71">T20</a>).</li>',
         '(<a href="/blog/developpement-odoo-2/rapports-qweb-pdf-en-odoo-19-iractionsreport-external-layout-et-wkhtmltopdf-71">Rapports QWeb PDF</a>).</li>',
         "R5 — code T remplacé par le titre de l'article visé"),
        ('ajouté en <a href="/blog/developpement-odoo-2/heritage-des-modeles-odoo-19-inherit-inherits-abstractmodel-64">T13</a>',
         'ajouté dans <a href="/blog/developpement-odoo-2/heritage-des-modeles-odoo-19-inherit-inherits-abstractmodel-64">Héritage des modèles</a>',
         "R5 — code T remplacé par le titre de l'article visé"),
        ('rapports QWeb vus en <a href="/blog/developpement-odoo-2/rapports-qweb-pdf-en-odoo-19-iractionsreport-external-layout-et-wkhtmltopdf-71">T20</a>)',
         '<a href="/blog/developpement-odoo-2/rapports-qweb-pdf-en-odoo-19-iractionsreport-external-layout-et-wkhtmltopdf-71">rapports QWeb PDF</a>)',
         "R5 — code T remplacé par le titre de l'article visé"),
    ],
    # 73 — Actions serveur, cron et automations en Odoo 19 : ir.cron, ir.actions.server et 
    73: [
        ('(<a href="/blog/developpement-odoo-2/email-templates-et-mailthread-en-odoo-19-envoi-automatique-depuis-create-et-write-72">T21</a>).',
         '(<a href="/blog/developpement-odoo-2/email-templates-et-mailthread-en-odoo-19-envoi-automatique-depuis-create-et-write-72">Email templates et mail.thread</a>).',
         "R5 — code T remplacé par le titre de l'article visé"),
        ('(<a href="/blog/developpement-odoo-2/methodes-de-modele-odoo-19-create-write-unlink-et-apimodel-create-multi-66">T15</a>).',
         '(<a href="/blog/developpement-odoo-2/methodes-de-modele-odoo-19-create-write-unlink-et-apimodel-create-multi-66">Méthodes de modèle</a>).',
         "R5 — code T remplacé par le titre de l'article visé"),
        (('comme vu en\n'
          '                                <a href="/blog/developpement-odoo-2/wizards-et-assistants-en-odoo-19-transientmodel-targetnew-et-binding-model-id-70">T19</a>'),
         ('comme vu dans\n'
          '                                <a href="/blog/developpement-odoo-2/wizards-et-assistants-en-odoo-19-transientmodel-targetnew-et-binding-model-id-70">Wizards et assistants</a>'),
         "R5 — code T remplacé par le titre de l'article visé"),
    ],
    # 74 — Controllers HTTP et API REST en Odoo 19 : http.Controller, @http.route et modes 
    74: [
        ('(<a href="/blog/developpement-odoo-2/actions-serveur-cron-et-automations-en-odoo-19-ircron-iractionsserver-et-baseautomation-73">T22</a>).',
         '(<a href="/blog/developpement-odoo-2/actions-serveur-cron-et-automations-en-odoo-19-ircron-iractionsserver-et-baseautomation-73">Actions serveur, cron et automations</a>).',
         "R5 — code T remplacé par le titre de l'article visé"),
        ('(<a href="/blog/developpement-odoo-2/rapports-qweb-pdf-en-odoo-19-iractionsreport-external-layout-et-wkhtmltopdf-71">T20</a>).',
         '(<a href="/blog/developpement-odoo-2/rapports-qweb-pdf-en-odoo-19-iractionsreport-external-layout-et-wkhtmltopdf-71">Rapports QWeb PDF</a>).',
         "R5 — code T remplacé par le titre de l'article visé"),
        ('bloc de T06 à T23. Tu',
         'bloc. Tu',
         'R5 — plage de codes T retirée'),
        (('<a href="/blog/developpement-odoo-2/actions-serveur-cron-et-automations-en-odoo-19-ircron-iractionsserver-et-baseautomation-73" class="btn btn-outline-secondary">\n'
          '                        &larr; T22 — Actions serveur &amp; cron\n'
          '                    </a>\n'
          '                    '),
         '',
         'R2 — lien « ← précédent » intra-série retiré ; le bouton « Récupérer le guide technique complet » (hors série) reste'),
    ],
    # 75 — Le recrutement dans Odoo 19 : du poste ouvert au contrat signé
    75: [
        ('<em>Article 1/3 de cette saison</em>',
         "<em>l'article sur les employés</em>",
         'R6 — numérotation « x/y » retirée ou reformulée'),
        ("l'article 3/3.",
         "l'article suivant.",
         'R6 — numérotation « x/y » retirée ou reformulée'),
    ],
    # 76 — Congés, absences et temps de présence dans Odoo 19
    76: [
        ('embauches (article 2/3).',
         "embauches (voir l'article sur le recrutement).",
         'R6 — numérotation « x/y » retirée ou reformulée'),
        ('fiche employé (article 1/3) et au',
         'fiche employé et au',
         'R6 — numérotation « x/y » retirée ou reformulée'),
        ("l'équipe</strong> (article 1/3),",
         "l'équipe</strong>,",
         'R6 — numérotation « x/y » retirée ou reformulée'),
        ('<strong>recruter</strong> (article 2/3)',
         '<strong>recruter</strong>',
         'R6 — numérotation « x/y » retirée ou reformulée'),
        ('complète (3/3).</strong>',
         'complète.</strong>',
         'R6 — numérotation « x/y » retirée ou reformulée'),
    ],
    # 77 — Créer un site vitrine professionnel avec Odoo 19
    77: [
        ('<strong>boutique eCommerce</strong> (article 3/4)',
         '<strong>boutique eCommerce</strong>',
         'R6 — numérotation « x/y » retirée ou reformulée'),
        ('Prochaine étape (S5·2/4) :',
         'Prochaine étape :',
         'R6 — numéro retiré du bloc « Prochaine étape » (le bloc et son résumé restent)'),
    ],
    # 78 — Blog professionnel et forum communautaire avec Odoo 19
    78: [
        ('est en ligne (article 1/4).',
         'est en ligne.',
         'R6 — numérotation « x/y » retirée ou reformulée'),
        ('pages vitrine (article 1/4) —',
         'pages vitrine —',
         'R6 — numérotation « x/y » retirée ou reformulée'),
        ('Prochaine étape (S5·3/4) :',
         'Prochaine étape :',
         'R6 — numéro retiré du bloc « Prochaine étape » (le bloc et son résumé restent)'),
    ],
    # 79 — Lancer une boutique eCommerce avec Odoo 19
    79: [
        ('site vitrine (1/4) et un blog éditorial (2/4).',
         'site vitrine et un blog éditorial.',
         'R6 — numérotation « x/y » retirée ou reformulée'),
        ('existant (article 1/3 de la Saison 1)',
         'existant (Saison 1)',
         'R6 — numérotation « x/y » retirée ou reformulée'),
        ('<code>website</code> (article 1/4)',
         '<code>website</code>',
         'R6 — numérotation « x/y » retirée ou reformulée'),
        ('Prochaine étape (S5·4/4) :',
         'Prochaine étape :',
         'R6 — numéro retiré du bloc « Prochaine étape » (le bloc et son résumé restent)'),
    ],
    # 80 — Créer une plateforme eLearning avec Odoo 19
    80: [
        ('Après le site vitrine (1/6), le blog (2/6) et la boutique (3/6),',
         'Après le site vitrine, le blog et la boutique,',
         'R6 — numérotation « x/y » retirée ou reformulée'),
        (('<code>website</code> (article 1/6\n'
          '                    de la Saison)'),
         '<code>website</code>',
         'R6 — numérotation « x/y » retirée ou reformulée'),
        ('Prochaine étape (S5·5/6) :',
         'Prochaine étape :',
         'R6 — numéro retiré du bloc « Prochaine étape » (le bloc et son résumé restent)'),
    ],
    # 81 — Organiser vos événements avec Odoo 19
    81: [
        (('<code>website</code> (article 1/6 de\n'
          '                    la Saison)'),
         '<code>website</code>',
         'R6 — numérotation « x/y » retirée ou reformulée'),
        ('Prochaine étape (S5·6/6) :',
         'Prochaine étape :',
         'R6 — numéro retiré du bloc « Prochaine étape » (le bloc et son résumé restent)'),
    ],
    # 83 — Lancer une campagne d'email marketing avec Odoo 19
    83: [
        (' (article 2/4 de cette saison)',
         '',
         'R6 — numérotation « x/y » retirée ou reformulée'),
        ('Prochaine étape (S6·2/4) :',
         'Prochaine étape :',
         'R6 — numéro retiré du bloc « Prochaine étape » (le bloc et son résumé restent)'),
    ],
    # 84 — SMS Marketing avec Odoo 19
    84: [
        ("Après l'email (article 1/4),",
         "Après l'email,",
         'R6 — numérotation « x/y » retirée ou reformulée'),
        (('(Marketing\n'
          '                    Automation 3/4)'),
         ('(Marketing\n'
          '                    Automation)'),
         'R6 — numérotation « x/y » retirée ou reformulée'),
        ('Prochaine étape (S6·3/4) :',
         'Prochaine étape :',
         'R6 — numéro retiré du bloc « Prochaine étape » (le bloc et son résumé restent)'),
    ],
    # 85 — Automatiser vos campagnes avec Odoo 19 CE
    85: [
        ('Prochaine étape (S6·4/4) :',
         'Prochaine étape :',
         'R6 — numéro retiré du bloc « Prochaine étape » (le bloc et son résumé restent)'),
    ],
    # 86 — Scoring et qualification des leads avec Odoo 19 CE
    86: [
        ('précédent (S6·3/4) :',
         'précédent :',
         'R6 — numérotation « x/y » retirée ou reformulée'),
    ],
    # 87 — Installer et configurer le POS avec Odoo 19
    87: [
        ('Prochaine étape (S7·2/3) :',
         'Prochaine étape :',
         'R6 — numéro retiré du bloc « Prochaine étape » (le bloc et son résumé restent)'),
        ("l'article suivant (S7·2/3).",
         "l'article suivant.",
         'R6 — numérotation « x/y » retirée ou reformulée'),
    ],
    # 88 — Encaisser au quotidien avec le POS d'Odoo 19
    88: [
        ('Prochaine étape (S7·3/3) :',
         'Prochaine étape :',
         'R6 — numéro retiré du bloc « Prochaine étape » (le bloc et son résumé restent)'),
    ],
    # 90 — Sécuriser Odoo 19 en production : Nginx, SSL Let's Encrypt et VPS Debian
    90: [
        ('(cf. article T01 de la série)',
         '(cf. <a href="/blog/developpement-odoo-2/installer-odoo-19-sur-ubuntu-2404-lts-50">Installer Odoo 19 sur Ubuntu</a>)',
         "R5 — code T remplacé par un lien vers l'article visé"),
        ('(cf. article T07 de la série)',
         '(cf. <a href="/blog/developpement-odoo-2/gestion-des-bases-de-donnees-odoo-19-57">Gestion des bases de données</a>)',
         "R5 — code T remplacé par un lien vers l'article visé"),
        ('Prochain article (T25) :',
         'Prochain article :',
         'R5 — code T retiré du bloc « Prochain article »'),
    ],
    # 97 — Variantes produit dans Odoo 19 CE — attributs, valeurs et prix par variante
    97: [
        ("l'article S9·2/4 sur les pricelists",
         "l'article sur les pricelists",
         'R6 — numérotation « x/y » retirée ou reformulée'),
    ],
    # 98 — Promotions multicanal dans Odoo 19 CE — Ventes B2B, eCommerce et Point de Vente
    98: [
        ("l'article <strong>S10·2/N</strong>.",
         "l'article suivant.",
         'R6 — numérotation « x/y » retirée ou reformulée'),
    ],
    # 103 — Pricelists & segmentation client dans Odoo 19 CE — Pro, VIP et Revendeur
    103: [
        ('Dans la <strong>Partie 3/3</strong> de la Saison 10',
         'Dans le <strong>prochain article</strong> de la Saison 10',
         'R6 — numérotation « x/y » retirée ou reformulée'),
    ],
    # 105 — Écrire des tests automatisés en Odoo 19 — TransactionCase, HttpCase, @tagged, Fo
    105: [
        ('(<a href="/blog/developpement-odoo-2/installer-odoo-19-sur-ubuntu-debian-guide-debutant-56">T01 Ubuntu</a> ou équivalent)',
         '(<a href="/blog/developpement-odoo-2/installer-odoo-19-sur-ubuntu-2404-lts-50">Installer Odoo 19 sur Ubuntu</a> ou équivalent)',
         "R5 — code T remplacé par le titre de l'article visé ; ancre d'origine vers le mauvais article, corrigée"),
    ],
    # 106 — Migration Odoo 18 → 19 — scripts pre, post, end et 7 breaking changes
    106: [
        ('(<a href="/blog/developpement-odoo-2/installer-odoo-19-sur-ubuntu-debian-guide-debutant-56">T01 Ubuntu</a>).',
         '(<a href="/blog/developpement-odoo-2/installer-odoo-19-sur-ubuntu-2404-lts-50">Installer Odoo 19 sur Ubuntu</a>).',
         "R5 — code T remplacé par le titre de l'article visé ; ancre d'origine vers le mauvais article, corrigée"),
        ('tests automatisés</a> (T24)',
         'tests automatisés</a>',
         "R5 — code T retiré (doublon d'un lien voisin ou article courant)"),
        ('(<a href="/blog/developpement-odoo-2/tests-automatises-odoo-19-105">T24</a>) qui',
         '(<a href="/blog/developpement-odoo-2/tests-automatises-odoo-19-105">Tests automatisés</a>) qui',
         "R5 — code T remplacé par le titre de l'article visé"),
    ],
    # 107 — OWL composants custom Odoo 19
    107: [
        ('<a href="/blog/developpement-odoo-2/installer-odoo-19-sur-ubuntu-debian-guide-debutant-56">T01</a>).',
         '<a href="/blog/developpement-odoo-2/installer-odoo-19-sur-ubuntu-2404-lts-50">Installer Odoo 19 sur Ubuntu</a>).',
         "R5 — code T remplacé par le titre de l'article visé ; ancre d'origine vers le mauvais article, corrigée"),
    ],
    # 108 — bus.bus + WebSocket temps réel en Odoo 19
    108: [
        ('<code>sla_badge</code> du <a href="/blog/developpement-odoo-2/owl-composants-custom-odoo-19-107" style="color:#ffc107;">T26</a>.',
         '<code>sla_badge</code> de l\'article <a href="/blog/developpement-odoo-2/owl-composants-custom-odoo-19-107" style="color:#ffc107;">OWL composants custom</a>.',
         "R5 — code T remplacé par le titre de l'article visé"),
        ('(<a href="/blog/developpement-odoo-2/installer-odoo-19-sur-ubuntu-debian-guide-debutant-56">T01</a>) avec',
         '(<a href="/blog/developpement-odoo-2/installer-odoo-19-sur-ubuntu-2404-lts-50">Installer Odoo 19 sur Ubuntu</a>) avec',
         "R5 — code T remplacé par le titre de l'article visé ; ancre d'origine vers le mauvais article, corrigée"),
        ('<code>sla_badge</code> du <a href="/blog/developpement-odoo-2/owl-composants-custom-odoo-19-107">T26</a>).',
         '<code>sla_badge</code> de l\'article <a href="/blog/developpement-odoo-2/owl-composants-custom-odoo-19-107">OWL composants custom</a>).',
         "R5 — code T remplacé par le titre de l'article visé"),
        ('(<a href="/blog/developpement-odoo-2/cycle-vie-donnees-create-write-unlink-odoo-65">T15</a>) et des widgets OWL (T26).',
         '(<a href="/blog/developpement-odoo-2/methodes-de-modele-odoo-19-create-write-unlink-et-apimodel-create-multi-66">Méthodes de modèle</a>) et des widgets OWL.',
         "R5 — code T remplacé par le titre de l'article visé ; ancre d'origine vers le mauvais article, corrigée"),
        ('<code>SlaBadgeField</code> (T26) devient',
         '<code>SlaBadgeField</code> (voir <a href="/blog/developpement-odoo-2/owl-composants-custom-odoo-19-107">OWL composants custom</a>) devient',
         "R5 — code T remplacé par un lien vers l'article visé"),
        (('l\'<a href="/blog/developpement-odoo-2/tests-automatises-odoo-19-105">article T24</a>\n'
          '                    sur les tests.'),
         'l\'<a href="/blog/developpement-odoo-2/tests-automatises-odoo-19-105">article sur les tests automatisés</a>.',
         "R5 — code T remplacé par le titre de l'article visé"),
        ('la suite T27 ajoute',
         'la suite de cet article ajoute',
         "R5 — code T de l'article courant reformulé"),
        ('pattern v19 utilisé par T26.',
         "pattern v19 utilisé dans l'article sur les composants OWL.",
         'R5 — code T reformulé'),
    ],
    # 109 — Mesurer la performance de bus.bus en Odoo 19
    109: [
        ('<a href="/blog/developpement-odoo-2/bus-bus-websocket-temps-reel-108" style="color:#ffc107;">T27</a> ?',
         '<a href="/blog/developpement-odoo-2/bus-bus-websocket-temps-reel-108" style="color:#ffc107;">bus.bus + WebSocket</a> ?',
         "R5 — code T remplacé par le titre de l'article visé"),
        ('(<a href="/blog/developpement-odoo-2/installer-odoo-19-sur-ubuntu-debian-guide-debutant-56">T01</a>) + module',
         '(<a href="/blog/developpement-odoo-2/installer-odoo-19-sur-ubuntu-2404-lts-50">Installer Odoo 19 sur Ubuntu</a>) + module',
         "R5 — code T remplacé par le titre de l'article visé ; ancre d'origine vers le mauvais article, corrigée"),
        ('minimum (<a href="/blog/developpement-odoo-2/bus-bus-websocket-temps-reel-108">T27</a>).',
         'minimum (<a href="/blog/developpement-odoo-2/bus-bus-websocket-temps-reel-108">bus.bus + WebSocket</a>).',
         "R5 — code T remplacé par le titre de l'article visé"),
        ('patterns <a href="/blog/developpement-odoo-2/cycle-vie-donnees-create-write-unlink-odoo-65">T15</a> (write override) et <a href="/blog/developpement-odoo-2/tests-automatises-odoo-19-105">T24</a> (tests).',
         'patterns <a href="/blog/developpement-odoo-2/methodes-de-modele-odoo-19-create-write-unlink-et-apimodel-create-multi-66">Méthodes de modèle</a> (write override) et <a href="/blog/developpement-odoo-2/tests-automatises-odoo-19-105">Tests automatisés</a>.',
         "R5 — code T remplacé par le titre de l'article visé ; ancre d'origine vers le mauvais article, corrigée"),
        ('coût du pattern T27 ?',
         'coût du pattern live ?',
         'R5 — code T reformulé (« pattern live », comme le chapeau)'),
        ('<code>write()</code> du <a href="/blog/developpement-odoo-2/cycle-vie-donnees-create-write-unlink-odoo-65">T15</a>',
         '<code>write()</code> vue dans <a href="/blog/developpement-odoo-2/methodes-de-modele-odoo-19-create-write-unlink-et-apimodel-create-multi-66">Méthodes de modèle</a>',
         "R5 — code T remplacé par le titre de l'article visé ; ancre d'origine vers le mauvais article, corrigée"),
        ('avant/après du T27 ne',
         'avant/après ne',
         "R5 — code T retiré (doublon d'un lien voisin ou article courant)"),
        ('<em>computed/stored</em> (T26) :',
         '<em>computed/stored</em> :',
         "R5 — code T retiré (doublon d'un lien voisin ou article courant)"),
        ('3 tickets T26 visibles',
         '3 tickets visibles',
         "R5 — code T retiré du texte alternatif de l'image"),
        ('<code>sla_badge</code> du T26).',
         '<code>sla_badge</code>).',
         "R5 — code T retiré (doublon d'un lien voisin ou article courant)"),
        ('la contrainte T15',
         'la contrainte <code>write()</code>',
         'R5 — code T reformulé'),
        ('activer le pattern T27 ?',
         'activer le pattern live ?',
         'R5 — code T reformulé'),
        ('le pattern T27 est viable',
         'le pattern live est viable',
         'R5 — code T reformulé'),
        ('Coût bus.bus T27 mesuré',
         'Coût bus.bus mesuré',
         "R5 — code T retiré (doublon d'un lien voisin ou article courant)"),
        ('<strong>lire T27 avant T28</strong>',
         '<strong>à lire avant cet article</strong>',
         'R5 — codes T reformulés'),
        (' (T24 → T28)',
         '',
         'R5 — plage de codes T retirée'),
    ],
    # 117 — Git & GitHub pour le dev Odoo : 20 commandes pour cloner, brancher, contribuer
    117: [
        ("<strong>l'épisode 2/5</strong>",
         '<strong>le deuxième épisode</strong>',
         'R6 — numérotation « x/y » retirée ou reformulée'),
    ],
    # 118 — Bash pour Odoo : 5 scripts qui font gagner 1 heure par jour
    118: [
        ("<strong>l'épisode 3/5</strong>",
         '<strong>le troisième épisode</strong>',
         'R6 — numérotation « x/y » retirée ou reformulée'),
    ],
    # 119 — odoo-bin shell : la console cachée d'Odoo et 15 patterns ORM essentiels
    119: [
        ("<strong>l'épisode 4/5 de la série",
         '<strong>le quatrième épisode de la série',
         'R6 — numérotation « x/y » retirée ou reformulée'),
    ],
    # 124 — Utilisateurs, groupes et droits d'accès dans Odoo 19 Community
    124: [
        (('<section class="s_progress_bar pb48 oe_structure_solo">\n'
          '  <div class="container">\n'
          '    <div class="row">\n'
          '      <div class="col-lg-10 mx-auto">\n'
          '        <p class="small text-muted mb-2">Saison 12 — Administrer Odoo 19 CE · 2 / 7</p>\n'
          '        <div class="progress" style="height:8px;">\n'
          '          <div class="progress-bar" role="progressbar" style="width:28.5%; background-color:#2c5f8a;" aria-valuenow="2" aria-valuemin="0" aria-valuemax="7"></div>\n'
          '        </div>\n'
          '      </div>\n'
          '    </div>\n'
          '  </div>\n'
          '</section>'),
         '',
         'R1 — barre de progression « x / 7 » de la Saison 12 retirée (repère de position, rendu par le module)'),
    ],
    # 126 — Plan comptable par société dans Odoo 19 Community
    126: [
        (('<section class="s_progress_bar pb48 oe_structure_solo">\n'
          '  <div class="container">\n'
          '    <div class="row">\n'
          '      <div class="col-lg-10 mx-auto">\n'
          '        <p class="small text-muted mb-2">Saison 12 — Administrer Odoo 19 CE · 3 / 7</p>\n'
          '        <div class="progress" style="height:8px;">\n'
          '          <div class="progress-bar" role="progressbar" style="width:42.8%; background-color:#2c5f8a;" aria-valuenow="3" aria-valuemin="0" aria-valuemax="7"></div>\n'
          '        </div>\n'
          '      </div>\n'
          '    </div>\n'
          '  </div>\n'
          '</section>'),
         '',
         'R1 — barre de progression « x / 7 » de la Saison 12 retirée (repère de position, rendu par le module)'),
    ],
    # 131 — Modèles de rapports et format d'impression dans Odoo 19 Community
    131: [
        (('<section class="s_progress_bar pb48 oe_structure_solo">\n'
          '  <div class="container">\n'
          '    <div class="row">\n'
          '      <div class="col-lg-10 mx-auto">\n'
          '        <p class="small text-muted mb-2">Saison 12 — Administrer Odoo 19 CE · 4 / 7</p>\n'
          '        <div class="progress" style="height:8px;">\n'
          '          <div class="progress-bar" role="progressbar" style="width:57.1%; background-color:#2c5f8a;" aria-valuenow="4" aria-valuemin="0" aria-valuemax="7"></div>\n'
          '        </div>\n'
          '      </div>\n'
          '    </div>\n'
          '  </div>\n'
          '</section>'),
         '',
         'R1 — barre de progression « x / 7 » de la Saison 12 retirée (repère de position, rendu par le module)'),
    ],
    # 134 — Paramétrer Ventes et Achats dans Odoo 19 Community
    134: [
        (('<section class="s_progress_bar pb48 oe_structure_solo">\n'
          '  <div class="container">\n'
          '    <div class="row">\n'
          '      <div class="col-lg-10 mx-auto">\n'
          '        <p class="small text-muted mb-2">Saison 12 — Administrer Odoo 19 CE · 5 / 7</p>\n'
          '        <div class="progress" style="height:8px;">\n'
          '          <div class="progress-bar" role="progressbar" style="width:71.4%; background-color:#2c5f8a;" aria-valuenow="5" aria-valuemin="0" aria-valuemax="7"></div>\n'
          '        </div>\n'
          '      </div>\n'
          '    </div>\n'
          '  </div>\n'
          '</section>'),
         '',
         'R1 — barre de progression « x / 7 » de la Saison 12 retirée (repère de position, rendu par le module)'),
    ],
    # 136 — Paramétrer Stock et Comptabilité dans Odoo 19 Community
    136: [
        (('<section class="s_progress_bar pb48 oe_structure_solo">\n'
          '  <div class="container">\n'
          '    <div class="row">\n'
          '      <div class="col-lg-10 mx-auto">\n'
          '        <p class="small text-muted mb-2">Saison 12 — Administrer Odoo 19 CE · 6 / 7</p>\n'
          '        <div class="progress" style="height:8px;">\n'
          '          <div class="progress-bar" role="progressbar" style="width:85.7%; background-color:#2c5f8a;" aria-valuenow="6" aria-valuemin="0" aria-valuemax="7"></div>\n'
          '        </div>\n'
          '      </div>\n'
          '    </div>\n'
          '  </div>\n'
          '</section>'),
         '',
         'R1 — barre de progression « x / 7 » de la Saison 12 retirée (repère de position, rendu par le module)'),
    ],
    # 137 — Checklist de mise en service d'Odoo 19 PME — 40 points
    137: [
        (('<section class="s_progress_bar pb48 oe_structure_solo">\n'
          '  <div class="container">\n'
          '    <div class="row">\n'
          '      <div class="col-lg-10 mx-auto">\n'
          '        <p class="small text-muted mb-2">Saison 12 — Administrer Odoo 19 CE · 7 / 7 · série complète</p>\n'
          '        <div class="progress" style="height:8px;">\n'
          '          <div class="progress-bar" role="progressbar" style="width:100%; background-color:#2c5f8a;" aria-valuenow="7" aria-valuemin="0" aria-valuemax="7"></div>\n'
          '        </div>\n'
          '      </div>\n'
          '    </div>\n'
          '  </div>\n'
          '</section>'),
         '',
         'R1 — barre de progression « x / 7 » de la Saison 12 retirée (repère de position, rendu par le module)'),
    ],
    # 154 — Configurer la gestion de restaurant dans Odoo 19 Community
    154: [
        ('Prochaine étape (Saison Restaurant · 2/6) :',
         'Prochaine étape :',
         'R6 — numéro retiré du bloc « Prochaine étape » (le bloc et son résumé restent)'),
        (('La suite de la Saison Restaurant arrive ; en\n'
          '            attendant, ces guides'),
         'Ces guides',
         "R6 — annonce « la suite arrive » périmée retirée (la série est complète et le module affiche l'étape suivante)"),
    ],
    # 155 — Le plan de salle du restaurant dans Odoo 19 Community
    155: [
        ('Prochaine étape (Saison Restaurant · 3/6) :',
         'Prochaine étape :',
         'R6 — numéro retiré du bloc « Prochaine étape » (le bloc et son résumé restent)'),
        ('<h2>Continuer la Saison Restaurant</h2>',
         '<h2>Continuer dans le hub Point de vente</h2>',
         "R2 — titre et phrase adaptés au seul lien hors série qui reste (titre repris de l'article 154)"),
        (('Reprends depuis la configuration initiale, ou\n'
          '            complète'),
         'Complète',
         "R2 — titre et phrase adaptés au seul lien hors série qui reste (titre repris de l'article 154)"),
        (('<a href="/blog/fonctionnel-odoo-1/configurer-la-gestion-de-restaurant-dans-odoo-19-community-154" class="btn btn-light btn-lg me-2 mb-2">\n'
          '                &larr; Configurer la gestion de restaurant\n'
          '            </a>\n'
          '            '),
         '',
         'R2 — lien « ← précédent » intra-série retiré ; le lien vers le hub Point de vente (hors série) reste'),
    ],
    # 156 — Prendre une commande à table et l'envoyer en cuisine dans Odoo 19 Community
    156: [
        ('Prochaine étape (Saison Restaurant · 4/6) :',
         'Prochaine étape :',
         'R6 — numéro retiré du bloc « Prochaine étape » (le bloc et son résumé restent)'),
        ('<h2>Continuer la Saison Restaurant</h2>',
         '<h2>Continuer dans le hub Point de vente</h2>',
         "R2 — titre et phrase adaptés au seul lien hors série qui reste (titre repris de l'article 154)"),
        ('Reprends le plan de salle, ou révise',
         'Révise',
         "R2 — titre et phrase adaptés au seul lien hors série qui reste (titre repris de l'article 154)"),
        (('<a href="/blog/fonctionnel-odoo-1/le-plan-de-salle-du-restaurant-dans-odoo-19-community-155" class="btn btn-light btn-lg me-2 mb-2">\n'
          '                &larr; Le plan de salle du restaurant\n'
          '            </a>\n'
          '            '),
         '',
         'R2 — lien « ← précédent » intra-série retiré ; le lien vers le hub Point de vente (hors série) reste'),
    ],
    # 157 — Partager l'addition, ajouter un pourboire et encaisser dans Odoo 19 Community
    157: [
        ('Prochaine étape (Saison Restaurant · 5/6) :',
         'Prochaine étape :',
         'R6 — numéro retiré du bloc « Prochaine étape » (le bloc et son résumé restent)'),
        ('<h2>Continuer la Saison Restaurant</h2>',
         '<h2>Continuer dans le hub Point de vente</h2>',
         "R2 — titre et phrase adaptés au seul lien hors série qui reste (titre repris de l'article 154)"),
        ('Reprends la prise de commande, ou révise',
         'Révise',
         "R2 — titre et phrase adaptés au seul lien hors série qui reste (titre repris de l'article 154)"),
        (('<a href="/blog/fonctionnel-odoo-1/prendre-une-commande-a-table-et-lenvoyer-en-cuisine-dans-odoo-19-community-156" class="btn btn-light btn-lg me-2 mb-2">\n'
          '                &larr; Commande à table &amp; cuisine\n'
          '            </a>\n'
          '            '),
         '',
         'R2 — lien « ← précédent » intra-série retiré ; le lien vers le hub Point de vente (hors série) reste'),
    ],
    # 158 — Composer la carte du restaurant dans Odoo 19 Community
    158: [
        ('Prochaine étape (Saison Restaurant · 6/6) :',
         'Prochaine étape :',
         'R6 — numéro retiré du bloc « Prochaine étape » (le bloc et son résumé restent)'),
        ('<h2>Continuer la Saison Restaurant</h2>',
         '<h2>Continuer dans le hub Point de vente</h2>',
         "R2 — titre et phrase adaptés au seul lien hors série qui reste (titre repris de l'article 154)"),
        ("Reprends l'encaissement, ou approfondis",
         'Approfondis',
         "R2 — titre et phrase adaptés au seul lien hors série qui reste (titre repris de l'article 154)"),
        (('<a href="/blog/fonctionnel-odoo-1/partager-laddition-ajouter-un-pourboire-et-encaisser-dans-odoo-19-community-157" class="btn btn-light btn-lg me-2 mb-2">\n'
          "                &larr; L'addition &amp; le paiement\n"
          '            </a>\n'
          '            '),
         '',
         'R2 — lien « ← précédent » intra-série retiré ; le lien vers le hub Point de vente (hors série) reste'),
    ],
    # 159 — Commande en libre-service par QR et clôture de la journée dans Odoo 19 Community
    159: [
        (('<section class="s_cta_box pt48 pb48 bg-primary text-white">\n'
          '    <div class="container text-center">\n'
          '        <h2>La Saison Restaurant, du début à la fin</h2>\n'
          '        <p class="lead">Le restaurant tourne en libre-service. Reprends la carte, ou repars de la\n'
          '            configuration initiale pour suivre toute la saison.</p>\n'
          '        <div class="mt-4">\n'
          '            <a href="/blog/fonctionnel-odoo-1/composer-la-carte-du-restaurant-dans-odoo-19-community-158" class="btn btn-light btn-lg me-2 mb-2">\n'
          '                &larr; La carte du restaurant\n'
          '            </a>\n'
          '            <a href="/blog/fonctionnel-odoo-1/configurer-la-gestion-de-restaurant-dans-odoo-19-community-154" class="btn btn-outline-light btn-lg mb-2">\n'
          '                Revenir au début de la saison &rarr;\n'
          '            </a>\n'
          '        </div>\n'
          '    </div>\n'
          '</section>'),
         '',
         'R2 — encadré « La Saison Restaurant, du début à la fin » retiré : ses deux liens sont intra-série (précédent, début de saison)'),
    ],
    # 169 — Quelle licence pour votre module Odoo 19 ?
    169: [
        ("L'article 2/3",
         "L'article suivant",
         'R6 — numérotation « x/y » retirée ou reformulée'),
    ],
    # 170 — __manifest__.py Odoo 19 décrypté
    170: [
        ('<td class="ok">Article 3/3</td>',
         '<td class="ok">Article suivant</td>',
         'R6 — numérotation « x/y » retirée ou reformulée'),
    ],
    # 171 — Publier un module sur l'Odoo Apps Store
    171: [
        ('le choix de licence (1/3) et la lecture du manifeste par le serveur (2/3).',
         'le choix de licence et la lecture du manifeste par le serveur.',
         'R6 — numérotation « x/y » retirée ou reformulée'),
        ("L'article 2/3 a établi",
         "L'article précédent a établi",
         'R6 — numérotation « x/y » retirée ou reformulée'),
        ("l'article 1/3 —",
         "l'article sur les licences —",
         'R6 — numérotation « x/y » retirée ou reformulée'),
        (("l'article\n"
          '                1/3 appelait'),
         "l'article sur les licences appelait",
         'R6 — numérotation « x/y » retirée ou reformulée'),
        (('<h3 class="text-center mb-4">La série « Licences &amp; distribution »</h3>\n'
          '                <div class="row">\n'
          '                    <div class="col-md-4">\n'
          '                        <div class="s_card p-3 h-100">\n'
          '                            <h5><a href="/blog/developpement-odoo-2/quelle-licence-pour-votre-module-odoo-19-169">1/3 — Quelle licence pour votre module ?</a></h5>\n'
          '                            <p class="small">Les 10 valeurs, la règle de contamination AGPL, et pourquoi une licence ne protège rien techniquement.</p>\n'
          '                        </div>\n'
          '                    </div>\n'
          '                    <div class="col-md-4">\n'
          '                        <div class="s_card p-3 h-100">\n'
          '                            <h5><a href="/blog/developpement-odoo-2/manifest-py-odoo-19-decrypte-170">2/3 — <code>__manifest__.py</code> décrypté</a></h5>\n'
          '                            <p class="small">Les 33 clés, la version qui rend un module invisible, les 3 formes d\'<code>auto_install</code>.</p>\n'
          '                        </div>\n'
          '                    </div>\n'
          '                    <div class="col-md-4">\n'
          '                        <div class="s_card p-3 h-100">\n'
          '                            <h5><a href="/blog/developpement-odoo-2/architecture-technique-odoo-56">'),
         ('<h3 class="text-center mb-4">À lire aussi</h3>\n'
          '                <div class="row">\n'
          '                    <div class="col-md-4">\n'
          '                        <div class="s_card p-3 h-100">\n'
          '                            <h5><a href="/blog/developpement-odoo-2/architecture-technique-odoo-56">'),
         'R4 — cartes des articles 1/3 et 2/3 retirées ; la carte hors série « Architecture technique Odoo 19 » reste, titre « À lire aussi »'),
    ],
    # 172 — Importer clients et fournisseurs dans Odoo 19 Community
    172: [
        (('<p class="mb-0"><strong>Article&nbsp;1/5</strong> — précédent&nbsp;: aucun, c\'est le point de\n'
          '                    départ. Suivant&nbsp;: <em>Importer son catalogue articles dans Odoo 19 Community</em>.</p>'),
         '',
         'R6 — paragraphe « Article 1/5 — précédent : aucun… Suivant : … » retiré (il ne fait que redire la navigation)'),
    ],
    # 173 — Importer son catalogue articles dans Odoo 19 Community
    173: [
        (('<section class="s_text_block pt8 pb24">\n'
          '    <div class="container">\n'
          '        <div class="row">\n'
          '            <div class="col-lg-10 mx-auto">\n'
          '                <h3>La série — Reprendre ses données dans Odoo 19</h3>\n'
          '                <ul>\n'
          '                    <li>Article 1/5 — Importer clients et fournisseurs.</li>\n'
          '                    <li><strong>Article 2/5 — Importer son catalogue articles</strong> — tu y es.</li>\n'
          '                    <li>Article 3/5 — Charger son stock initial.</li>\n'
          "                    <li>Article 4/5 — Reprendre sa balance d'ouverture.</li>\n"
          '                    <li>Article 5/5 — Recetter sa reprise de données.</li>\n'
          '                </ul>\n'
          '                <p class="mb-0"><strong>Article&nbsp;2/5</strong> — précédent&nbsp;:\n'
          '                    <em>Importer clients et fournisseurs dans Odoo 19 Community</em>. Suivant&nbsp;:\n'
          '                    <em>Charger son stock initial dans Odoo 19 Community</em>.</p>\n'
          '            </div>\n'
          '        </div>\n'
          '    </div>\n'
          '</section>'),
         '',
         'R4 — section « La série » retirée entière avec son paragraphe « Article x/5 — précédent… Suivant… » (navigation seule)'),
    ],
    # 174 — Charger son stock initial dans Odoo 19 Community
    174: [
        (('<section class="s_text_block pt8 pb24">\n'
          '    <div class="container">\n'
          '        <div class="row">\n'
          '            <div class="col-lg-10 mx-auto">\n'
          '                <h3>La série — Reprendre ses données dans Odoo 19</h3>\n'
          '                <ul>\n'
          '                    <li>Article 1/5 — Importer clients et fournisseurs.</li>\n'
          '                    <li>Article 2/5 — Importer son catalogue articles.</li>\n'
          '                    <li><strong>Article 3/5 — Charger son stock initial</strong> — tu y es.</li>\n'
          "                    <li>Article 4/5 — Reprendre sa balance d'ouverture.</li>\n"
          '                    <li>Article 5/5 — Recetter sa reprise de données.</li>\n'
          '                </ul>\n'
          '                <p class="mb-0"><strong>Article&nbsp;3/5</strong> — précédent&nbsp;:\n'
          '                    <em>Importer son catalogue articles dans Odoo 19 Community</em>. Suivant&nbsp;:\n'
          "                    <em>Reprendre sa balance d'ouverture dans Odoo 19 Community</em>.</p>\n"
          '            </div>\n'
          '        </div>\n'
          '    </div>\n'
          '</section>'),
         '',
         'R4 — section « La série » retirée entière avec son paragraphe « Article x/5 — précédent… Suivant… » (navigation seule)'),
    ],
    # 175 — Reprendre sa balance d'ouverture dans Odoo 19 Community
    175: [
        (('<section class="s_text_block pt8 pb24">\n'
          '    <div class="container">\n'
          '        <div class="row">\n'
          '            <div class="col-lg-10 mx-auto">\n'
          '                <h3>La série — Reprendre ses données dans Odoo 19</h3>\n'
          '                <ul>\n'
          '                    <li>Article 1/5 — Importer clients et fournisseurs.</li>\n'
          '                    <li>Article 2/5 — Importer son catalogue articles.</li>\n'
          '                    <li>Article 3/5 — Charger son stock initial.</li>\n'
          "                    <li><strong>Article 4/5 — Reprendre sa balance d'ouverture</strong> — tu y es.</li>\n"
          '                    <li>Article 5/5 — Recetter sa reprise de données.</li>\n'
          '                </ul>\n'
          '                <p class="mb-0"><strong>Article&nbsp;4/5</strong> — précédent&nbsp;:\n'
          '                    <em>Charger son stock initial dans Odoo 19 Community</em>. Suivant&nbsp;:\n'
          '                    <em>Recetter sa reprise de données dans Odoo 19 Community</em>.</p>\n'
          '            </div>\n'
          '        </div>\n'
          '    </div>\n'
          '</section>'),
         '',
         'R4 — section « La série » retirée entière avec son paragraphe « Article x/5 — précédent… Suivant… » (navigation seule)'),
    ],
    # 176 — Recetter sa reprise de données dans Odoo 19 Community
    176: [
        (('<section class="s_text_block pt8 pb24">\n'
          '    <div class="container">\n'
          '        <div class="row">\n'
          '            <div class="col-lg-10 mx-auto">\n'
          '                <h3>La série — Reprendre ses données dans Odoo 19</h3>\n'
          '                <ul>\n'
          '                    <li>Article 1/5 — Importer clients et fournisseurs.</li>\n'
          '                    <li>Article 2/5 — Importer son catalogue articles.</li>\n'
          '                    <li>Article 3/5 — Charger son stock initial.</li>\n'
          "                    <li>Article 4/5 — Reprendre sa balance d'ouverture.</li>\n"
          '                    <li><strong>Article 5/5 — Recetter sa reprise de données</strong> — tu y es.</li>\n'
          '                </ul>\n'
          '                <p class="mb-0"><strong>Article&nbsp;5/5</strong> — précédent&nbsp;:\n'
          "                    <em>Reprendre sa balance d'ouverture dans Odoo 19 Community</em>. Dernier article de la\n"
          '                    série.</p>\n'
          '            </div>\n'
          '        </div>\n'
          '    </div>\n'
          '</section>'),
         '',
         'R4 — section « La série » retirée entière avec son paragraphe « Article x/5 — précédent… Suivant… » (navigation seule)'),
    ],
}

DROP = {
    74: [
        # la section contient le lien hors série vers /guide-technique-odoo : seul le lien « précédent » part (CURATED)
        'Récupérer le guide technique complet',
    ],
    124: [
        # bandeau de la barre de progression : la section entière part (CURATED)
        'Saison 12 — Administrer Odoo 19 CE · 2 / 7</p>',
    ],
    126: [
        # bandeau de la barre de progression : la section entière part (CURATED)
        'Saison 12 — Administrer Odoo 19 CE · 3 / 7</p>',
    ],
    131: [
        # bandeau de la barre de progression : la section entière part (CURATED)
        'Saison 12 — Administrer Odoo 19 CE · 4 / 7</p>',
    ],
    134: [
        # bandeau de la barre de progression : la section entière part (CURATED)
        'Saison 12 — Administrer Odoo 19 CE · 5 / 7</p>',
    ],
    136: [
        # bandeau de la barre de progression : la section entière part (CURATED)
        'Saison 12 — Administrer Odoo 19 CE · 6 / 7</p>',
    ],
    137: [
        # bandeau de la barre de progression : la section entière part (CURATED)
        'Saison 12 — Administrer Odoo 19 CE · 7 / 7 · série complète</p>',
    ],
    155: [
        # le bloc de liens mêle un lien hors série (hub Point de vente) : seul le lien « précédent » part (CURATED)
        'Installer et configurer le POS &rarr;',
    ],
    156: [
        # le bloc de liens mêle un lien hors série (hub Point de vente) : seul le lien « précédent » part (CURATED)
        'Encaisser au quotidien &rarr;',
    ],
    157: [
        # le bloc de liens mêle un lien hors série (hub Point de vente) : seul le lien « précédent » part (CURATED)
        'Encaisser au quotidien &rarr;',
    ],
    158: [
        # le bloc de liens mêle un lien hors série (hub Point de vente) : seul le lien « précédent » part (CURATED)
        'Catalogue avancé au POS &rarr;',
    ],
    159: [
        # remplacé par la suppression de toute la section (CURATED) : sans liens, la phrase d'appel n'a plus d'objet
        'Revenir au début de la saison &rarr;',
    ],
    171: [
        # la grille contient une carte hors série : seules les cartes de la série partent (CURATED)
        'La série « Licences &amp; distribution »</h3>',
    ],
    173: [
        # remplacé par la suppression de toute la section (CURATED)
        '<h3>La série — Reprendre ses données dans Odoo 19</h3>',
    ],
    174: [
        # remplacé par la suppression de toute la section (CURATED)
        '<h3>La série — Reprendre ses données dans Odoo 19</h3>',
    ],
    175: [
        # remplacé par la suppression de toute la section (CURATED)
        '<h3>La série — Reprendre ses données dans Odoo 19</h3>',
    ],
    176: [
        # remplacé par la suppression de toute la section (CURATED)
        '<h3>La série — Reprendre ses données dans Odoo 19</h3>',
    ],
}

# Aucun résidu admis : tous les marqueurs détectés hors code sont traités.
ACCEPTED_RESIDUE = {}

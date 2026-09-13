"""Application du nettoyage des repères de série dans la base (tools/markers_apply.py).

Extraits réels de l'instantané de production (articles cités en commentaire). Le contenu est
forcé en SQL sur deux clés de langue, comme en production (jsonb en_US + fr_FR identiques)."""
import contextlib
import io
import json
import os
import shutil
import tempfile
from unittest.mock import patch

from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged

from odoo.addons.oski_blog_series.tools import markers, markers_apply, markers_curated

# Article 65 : bandeau numéroté avec thème
EYEBROW_65 = '<p class="text-uppercase small mb-2 text-warning">Bloc 3 · Framework ORM — Article 7/8</p>\n'

BODY = '<section class="s_text_block pt32 pb32"><p>Contenu de l\'article.</p></section>\n'

# Article 45 : navigation seule
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
</section>
"""

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
                </div>
            </div>
        </div>
    </div>
</section>
"""

# Article 51 : lien vers la saison suivante, gardé (DROP) mais relibellé (CURATED)
NEXT_SEASON_51 = """<section class="s_cta_box pt32 pb32 bg-light">
    <div class="container text-center">
        <p class="mb-2"><em>Article suivant :</em></p>
        <a href="/blog/fonctionnel-odoo-1/les-employes-dans-odoo-19-departements-postes-et-fiches-rh-58" class="btn btn-primary">Article 12 : Les employés →</a>
    </div>
</section>
"""

NAV_HREF = 'les-achats-dans-odoo-19-fournisseurs-commandes-et-reception-44'


@tagged('post_install', '-at_install')
class TestMarkersApplyInDatabase(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Blog, Series = cls.env['blog.blog'], cls.env['oski.blog.series']
        cls.blog = Blog.create({'name': 'Blog nettoyage'})
        cls.other_blog = Blog.create({'name': 'Autre blog nettoyage'})
        cls.series = Series.create({'name': 'Série nettoyage', 'blog_id': cls.blog.id})
        cls.other_series = Series.create({'name': 'Autre série nettoyage', 'blog_id': cls.other_blog.id})

        def post(name, blog, series, html):
            record = cls.env['blog.post'].create({
                'name': name, 'blog_id': blog.id, 'series_id': series.id if series else False})
            cls._force_content(record, {'en_US': html, 'fr_FR': html})
            return record

        cls.serial_html = EYEBROW_65 + BODY + NAV_45 + SEE_ALSO_65
        cls.serial = post('En série', cls.blog, cls.series, cls.serial_html)
        cls.standalone_html = BODY + NAV_45
        cls.standalone = post('Hors série', cls.blog, None, cls.standalone_html)
        cls.foreign_html = EYEBROW_65 + BODY + NAV_45
        cls.foreign = post('Autre blog', cls.other_blog, cls.other_series, cls.foreign_html)

    @classmethod
    def _force_content(cls, record, content):
        cls.env.flush_all()
        cls.env.cr.execute("UPDATE blog_post SET content = %s::jsonb WHERE id = %s",
                           (json.dumps(content), record.id))
        cls.env['blog.post'].invalidate_model(['content'])

    def setUp(self):
        super().setUp()
        self.backup_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.backup_dir, True)

    def _content(self, record):
        self.env.cr.execute("SELECT content FROM blog_post WHERE id = %s", (record.id,))
        return self.env.cr.fetchone()[0]

    def _run(self, **kwargs):
        kwargs.setdefault('blog_id', self.blog.id)
        kwargs.setdefault('backup_dir', self.backup_dir)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            result = markers_apply.run(self.env, **kwargs)
        return result, out.getvalue()

    def _backups(self):
        return sorted(os.listdir(self.backup_dir))

    # --- aperçu -------------------------------------------------------------------------

    def test_preview_writes_nothing(self):
        before = self._content(self.serial)
        result, output = self._run()
        self.assertEqual(self._content(self.serial), before)
        self.assertEqual(self._backups(), [])
        self.assertEqual(result['written'], [])
        counts = result['blogs'][self.blog.id]
        self.assertEqual((counts['to_change'], counts['edits'], counts['already'], counts['problems'],
                          counts['residue']), (1, 3, 0, 0, 0))
        self.assertIn('RESULT', output)

    def test_build_plan_covers_every_language_key(self):
        plan, problems = markers_apply.build_plan(self.env, blog_id=self.blog.id)
        self.assertEqual(problems, [])
        self.assertEqual(set(plan), {self.serial.id})
        entry = plan[self.serial.id]
        self.assertEqual([edit.rule for edit in entry['edits']], ['R1', 'R2', 'R3'])
        self.assertEqual(set(entry['langs']), {'en_US', 'fr_FR'})
        self.assertEqual(entry['langs']['en_US'], entry['langs']['fr_FR'])

    # --- application --------------------------------------------------------------------

    def test_apply_rewrites_both_languages_removes_markers_and_backs_up(self):
        result, output = self._run(apply=True)
        self.assertEqual(result['written'], [self.serial.id])
        content = self._content(self.serial)
        self.assertEqual(set(content), {'en_US', 'fr_FR'})
        self.assertEqual(content['en_US'], content['fr_FR'])
        html = content['en_US']
        self.assertIn('>Framework ORM</p>', html)
        self.assertIn("Contenu de l'article.", html)
        for marker in ('Article 7/8', NAV_HREF, 'Voir aussi dans cette série', 'T11'):
            self.assertNotIn(marker, html)
        self.assertEqual(markers.residual_markers(html), [])
        # l'ORM relit la valeur écrite en SQL
        self.assertNotIn('Article 7/8', self.serial.content)

        self.assertEqual(len(self._backups()), 1)
        backup = os.path.join(self.backup_dir, self._backups()[0])
        self.assertEqual(result['backup'], backup)
        self.assertRegex(os.path.basename(backup), r'^blog-markers-\d{8}-\d{6}\.json$')
        with open(backup) as handle:
            saved = json.load(handle)
        self.assertEqual(saved, {str(self.serial.id): {'en_US': self.serial_html, 'fr_FR': self.serial_html}})
        self.assertIn(backup, output)

    def test_post_without_series_keeps_its_navigation(self):
        self._run(apply=True)
        self.assertEqual(self._content(self.standalone),
                         {'en_US': self.standalone_html, 'fr_FR': self.standalone_html})

    def test_blog_id_limits_the_scope(self):
        plan, _problems = markers_apply.build_plan(self.env, blog_id=self.other_blog.id)
        self.assertEqual(set(plan), {self.foreign.id})
        plan, _problems = markers_apply.build_plan(self.env, blog_id=self.blog.id)
        self.assertNotIn(self.foreign.id, plan)
        self._run(apply=True)
        self.assertEqual(self._content(self.foreign), {'en_US': self.foreign_html, 'fr_FR': self.foreign_html})

    # --- idempotence --------------------------------------------------------------------

    def _curated(self):
        return {self.serial.id: [
            ("<p>Contenu de l'article.</p>", "<p>Contenu relu.</p>", 'R6 — remplacement de test'),
            ('<p class="small text-muted">Many2one, One2many, Many2many</p>', '', 'M — suppression de test'),
        ]}

    def test_second_pass_counts_already_and_writes_nothing(self):
        # la suppression manuelle vise un texte déjà dans la section R3 : on la sort de la section
        html = EYEBROW_65 + BODY + NAV_45 + '<p class="small text-muted">Many2one, One2many, Many2many</p>\n'
        self._force_content(self.serial, {'en_US': html, 'fr_FR': html})
        with patch.dict(markers_curated.CURATED, self._curated()):
            first, _output = self._run(apply=True)
            self.assertEqual(first['written'], [self.serial.id])
            cleaned = self._content(self.serial)
            self.assertIn('<p>Contenu relu.</p>', cleaned['en_US'])
            self.assertNotIn('Many2one', cleaned['en_US'])
            self.env.cr.execute("SELECT write_date FROM blog_post WHERE id = %s", (self.serial.id,))
            write_date = self.env.cr.fetchone()[0]

            second, output = self._run(apply=True)
        self.assertEqual(second['written'], [])
        self.assertIsNone(second['backup'])
        counts = second['blogs'][self.blog.id]
        self.assertEqual((counts['to_change'], counts['already'], counts['problems']), (0, 1, 0))
        self.assertEqual(self._content(self.serial), cleaned)
        self.env.cr.execute("SELECT write_date FROM blog_post WHERE id = %s", (self.serial.id,))
        self.assertEqual(self.env.cr.fetchone()[0], write_date)
        self.assertEqual(len(self._backups()), 1)
        self.assertIn('RESULT', output)

    def test_partial_state_is_a_problem(self):
        html = EYEBROW_65 + BODY + NAV_45 + '<p class="small text-muted">Many2one, One2many, Many2many</p>\n'
        self._force_content(self.serial, {'en_US': html, 'fr_FR': html})
        with patch.dict(markers_curated.CURATED, self._curated()):
            self._run(apply=True)
            # quelqu'un a remis un seul des remplacements : l'article est à moitié nettoyé
            half = self._content(self.serial)['en_US'].replace("<p>Contenu relu.</p>", "<p>Contenu de l'article.</p>")
            self._force_content(self.serial, {'en_US': half, 'fr_FR': half})
            result, _output = self._run()
            self.assertEqual(result['blogs'][self.blog.id]['problems'], 1)
            self.assertIn('[%s]' % self.serial.id, '\n'.join(result['problems']))
            with self.assertRaises(UserError):
                self._run(apply=True)
        self.assertEqual(self._content(self.serial), {'en_US': half, 'fr_FR': half})
        self.assertEqual(len(self._backups()), 1)

    def test_non_idempotent_plan_is_refused_before_writing(self):
        # 51 : le lien gardé (DROP) perd son extrait sous le remplacement manuel, un second
        # passage proposerait alors de supprimer la section.
        html = BODY + NEXT_SEASON_51
        self._force_content(self.serial, {'en_US': html, 'fr_FR': html})
        curated = {self.serial.id: [
            ('<em>Article suivant :</em>', '<em>Saison suivante :</em>', 'R2 — lien hors série conservé'),
            ('>Article 12 : Les employés →</a>', '>Les employés →</a>', 'R6 — « Article N » retiré'),
        ]}
        with patch.dict(markers_curated.CURATED, curated), \
                patch.dict(markers_curated.DROP, {self.serial.id: ['Article 12 : Les employés']}):
            result, _output = self._run()
            self.assertEqual(result['blogs'][self.blog.id]['problems'], 1)
            self.assertIn('idempotent', '\n'.join(result['problems']))
            with self.assertRaises(UserError):
                self._run(apply=True)
        self.assertEqual(self._content(self.serial), {'en_US': html, 'fr_FR': html})
        self.assertEqual(self._backups(), [])

    # --- refus --------------------------------------------------------------------------

    def test_missing_old_raises_and_writes_nothing(self):
        curated = {self.serial.id: [('<p>Paragraphe absent.</p>', '<p>Autre.</p>', 'M — absent')]}
        with patch.dict(markers_curated.CURATED, curated):
            result, _output = self._run()
            self.assertEqual(result['blogs'][self.blog.id]['problems'], 1)
            with self.assertRaises(UserError):
                self._run(apply=True)
        self.assertEqual(self._content(self.serial), {'en_US': self.serial_html, 'fr_FR': self.serial_html})
        self.assertEqual(self._backups(), [])

    def test_languages_that_differ_are_refused(self):
        self._force_content(self.serial, {'en_US': self.serial_html, 'fr_FR': self.serial_html + '<p>fr</p>'})
        _plan, problems = markers_apply.build_plan(self.env, blog_id=self.blog.id)
        self.assertEqual(len(problems), 1)
        with self.assertRaises(UserError):
            self._run(apply=True)
        self.assertEqual(self._backups(), [])

    def test_unaccepted_residue_is_a_problem_unless_accepted(self):
        html = BODY + '<p>La suite viendra avec T11 plus tard.</p>\n'
        self._force_content(self.standalone, {'en_US': html, 'fr_FR': html})
        result, _output = self._run()
        counts = result['blogs'][self.blog.id]
        self.assertEqual((counts['residue'], counts['problems']), (1, 1))
        with self.assertRaises(UserError):
            self._run(apply=True)
        self.assertEqual(self._backups(), [])
        with patch.dict(markers_curated.ACCEPTED_RESIDUE, {self.standalone.id: markers.residual_markers(html)}):
            result, _output = self._run()
        counts = result['blogs'][self.blog.id]
        self.assertEqual((counts['residue'], counts['problems']), (0, 0))

    def test_backup_failure_writes_nothing(self):
        with self.assertRaises(UserError):
            self._run(apply=True, backup_dir=os.path.join(self.backup_dir, 'absent'))
        self.assertEqual(self._content(self.serial), {'en_US': self.serial_html, 'fr_FR': self.serial_html})

    def test_content_changed_since_plan_is_refused(self):
        original_scan = markers_apply._scan

        def scan_then_edit(env, blog_id=None):
            rows = original_scan(env, blog_id)
            changed = self.serial_html + '<p>Modifié entre-temps.</p>'
            env.cr.execute("UPDATE blog_post SET content = %s::jsonb WHERE id = %s",
                           (json.dumps({'en_US': changed, 'fr_FR': changed}), self.serial.id))
            return rows

        with patch.object(markers_apply, '_scan', scan_then_edit), self.assertRaises(UserError):
            self._run(apply=True)
        self.assertEqual(self._backups(), [])

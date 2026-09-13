from datetime import datetime

from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged

from odoo.addons.oski_blog_series.tools import backfill

PAST = datetime(2026, 4, 26, 6, 57)


@tagged('post_install', '-at_install')
class TestBackfill(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.blog = cls.env['blog.blog'].create({'name': 'Blog reprise'})
        cls.other_blog = cls.env['blog.blog'].create({'name': 'Autre blog reprise'})
        cls.tag = cls.env['blog.tag'].create({'name': 'serie-test-reprise'})

        def post(name, content='<p>x</p>', blog=None):
            return cls.env['blog.post'].create({
                'name': name, 'blog_id': (blog or cls.blog).id, 'content': content,
                'is_published': True, 'post_date': PAST})

        cls.intro = post('Intro')
        cls.second = post('Deux', '<p>Saison 1 · Article 2/2</p>')
        cls.first = post('Un', '<p>Saison 1 · Article 1/2</p>')
        cls.standalone = post('Hors série')
        cls.foreign = post('Autre blog', blog=cls.other_blog)
        cls.version = cls.env.ref('oski_blog_series.odoo_version_19')

    def _specs(self, **overrides):
        spec = {
            'name': 'Série reprise', 'blog': self.blog.id, 'version': '19.0',
            'audience': 'Débutant', 'description': 'Description reprise', 'tag': 'serie-test-reprise',
            'blocks': [('Bloc un', [self.intro.id]), ('Bloc deux', [self.second.id, self.first.id])],
        }
        spec.update(overrides)
        return [spec]

    def test_plan_orders_by_block_then_marker_and_writes_nothing(self):
        plan, problems, leftovers = backfill.build_plan(self.env, self._specs())
        self.assertEqual(problems, [])
        rows = plan[0]['rows']
        self.assertEqual([r['post'] for r in rows], [self.intro, self.first, self.second])
        self.assertEqual([r['position'] for r in rows], [1, 2, 3])
        self.assertEqual([r['block'] for r in rows], ['Bloc un', 'Bloc deux', 'Bloc deux'])
        self.assertEqual(plan[0]['version'], self.version)
        self.assertEqual(plan[0]['tag'], self.tag)
        self.assertIn(self.standalone, leftovers)
        self.assertFalse(self.env['oski.blog.series'].search([('name', '=', 'Série reprise')]))
        self.assertFalse(self.first.series_id)

    def test_problems_are_reported(self):
        specs = self._specs(tag='etiquette-inexistante', blocks=[(None, [self.intro.id, self.foreign.id, 999999])])
        specs.append(dict(specs[0], name='Doublon', tag=None, blocks=[(None, [self.intro.id])]))
        _plan, problems, _leftovers = backfill.build_plan(self.env, specs)
        report = '\n'.join(problems)
        self.assertIn('etiquette-inexistante', report)
        self.assertIn('999999', report)
        self.assertIn(str(self.foreign.id), report)
        self.assertIn('deux séries', report)

    def test_apply_writes_series_and_is_idempotent(self):
        backfill.run(self.env, self._specs(), apply=True)
        backfill.run(self.env, self._specs(), apply=True)
        series = self.env['oski.blog.series'].search([('name', '=', 'Série reprise')])
        self.assertEqual(len(series), 1)
        self.assertEqual(series.tag_id, self.tag)
        self.assertEqual(series.odoo_version_id, self.version)
        self.assertEqual((self.intro.series_position, self.first.series_position, self.second.series_position), (1, 2, 3))
        self.assertEqual(self.second.series_block, 'Bloc deux')
        self.assertEqual(series._oski_published_posts(), self.intro | self.first | self.second)

    def test_apply_refuses_when_preview_has_problems(self):
        with self.assertRaises(UserError):
            backfill.run(self.env, self._specs(blocks=[(None, [999999])]), apply=True)
        self.assertFalse(self.env['oski.blog.series'].search([('name', '=', 'Série reprise')]))

    def test_report_is_readable(self):
        report = backfill.run(self.env, self._specs())
        self.assertIn('== Série reprise', report)
        self.assertIn('bloc « Bloc deux »', report)
        self.assertIn('marqueur 1/2', report)
        self.assertIn('PROBLÈMES : 0', report)
        self.assertIn('HORS SÉRIE', report)

    def test_marker_read_from_french_translation_when_active(self):
        self.env['res.lang']._activate_lang('fr_FR')
        other = self.env['blog.post'].create({
            'name': 'Trois', 'blog_id': self.blog.id, 'content': '<p>sans marqueur</p>',
            'is_published': True, 'post_date': PAST})
        other.with_context(lang='fr_FR').write({'content': '<p>Saison 1 · Article 1/2</p>'})
        specs = self._specs(blocks=[(None, [other.id, self.intro.id])])
        plan, problems, _leftovers = backfill.build_plan(self.env, specs)
        self.assertEqual(problems, [])
        rows = plan[0]['rows']
        self.assertEqual([r['post'] for r in rows], [other, self.intro])
        self.assertEqual(rows[0]['marker'], '1/2')

    def test_tag_found_by_french_name_when_active(self):
        self.env['res.lang']._activate_lang('fr_FR')
        tag = self.env['blog.tag'].create({'name': 'etiquette-en-anglais'})
        tag.with_context(lang='fr_FR').write({'name': 'etiquette-en-francais'})
        specs = self._specs(tag='etiquette-en-francais')
        plan, problems, _leftovers = backfill.build_plan(self.env, specs)
        self.assertEqual(problems, [])
        self.assertEqual(plan[0]['tag'], tag)

    def test_production_mapping_is_consistent(self):
        from odoo.addons.oski_blog_series.tools.backfill_mapping import SERIES
        ids = [pid for spec in SERIES for _block, block_ids in spec['blocks'] for pid in block_ids]
        self.assertEqual(len(ids), len(set(ids)), "un article figure dans deux séries")
        self.assertEqual(len(SERIES), 23)
        self.assertTrue(all(spec['description'] and spec['audience'] for spec in SERIES))

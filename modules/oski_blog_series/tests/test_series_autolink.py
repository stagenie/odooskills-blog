from psycopg2 import IntegrityError

from odoo.tests import TransactionCase, tagged
from odoo.tools import mute_logger


@tagged('post_install', '-at_install')
class TestSeriesAutolink(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Post = cls.env['blog.post']
        cls.Series = cls.env['oski.blog.series']
        cls.blog_dev = cls.env['blog.blog'].create({'name': 'Dév test'})
        cls.blog_fonc = cls.env['blog.blog'].create({'name': 'Fonc test'})
        cls.tag = cls.env['blog.tag'].create({'name': 'serie-test-autolink'})
        cls.other_tag = cls.env['blog.tag'].create({'name': 'serie-test-autre'})
        cls.series = cls.Series.create({
            'name': 'Série étiquetée', 'blog_id': cls.blog_dev.id, 'tag_id': cls.tag.id,
            'sequence': 20})

    def _post(self, **vals):
        values = {'name': 'Article', 'blog_id': self.blog_dev.id, 'content': '<p>x</p>'}
        values.update(vals)
        return self.Post.create(values)

    def test_tag_links_post_of_same_blog_with_next_position(self):
        first = self._post(tag_ids=[(6, 0, self.tag.ids)])
        second = self._post(tag_ids=[(6, 0, self.tag.ids)])
        self.assertEqual(first.series_id, self.series)
        self.assertEqual((first.series_position, second.series_position), (1, 2))

    def test_batch_create_gets_distinct_positions(self):
        posts = self.Post.create([
            {'name': 'Lot %s' % i, 'blog_id': self.blog_dev.id, 'content': '<p>x</p>',
             'tag_ids': [(6, 0, self.tag.ids)]}
            for i in range(3)])
        self.assertEqual(posts.mapped('series_position'), [1, 2, 3])

    def test_tag_on_other_blog_is_ignored(self):
        post = self._post(blog_id=self.blog_fonc.id, tag_ids=[(6, 0, self.tag.ids)])
        self.assertFalse(post.series_id)

    def test_lowest_sequence_wins(self):
        first_in_order = self.Series.create({
            'name': 'Prioritaire', 'blog_id': self.blog_dev.id, 'tag_id': self.other_tag.id,
            'sequence': 5})
        post = self._post(tag_ids=[(6, 0, (self.tag | self.other_tag).ids)])
        self.assertEqual(post.series_id, first_in_order)

    def test_explicit_series_is_never_overwritten(self):
        chosen = self.Series.create({'name': 'Choisie', 'blog_id': self.blog_dev.id})
        post = self._post(series_id=chosen.id, tag_ids=[(6, 0, self.tag.ids)])
        self.assertEqual(post.series_id, chosen)
        self.assertEqual(post.series_position, 1)
        post.write({'name': 'Renommé', 'tag_ids': [(6, 0, self.tag.ids)]})
        self.assertEqual(post.series_id, chosen)

    def test_tag_added_later_links_post(self):
        post = self._post()
        self.assertFalse(post.series_id)
        post.write({'tag_ids': [(4, self.tag.id)]})
        self.assertEqual(post.series_id, self.series)
        self.assertEqual(post.series_position, 1)

    def test_removing_tag_keeps_series(self):
        post = self._post(tag_ids=[(6, 0, self.tag.ids)])
        post.write({'tag_ids': [(5, 0, 0)]})
        self.assertEqual(post.series_id, self.series)

    def test_series_cleared_by_hand_stays_empty(self):
        post = self._post(tag_ids=[(6, 0, self.tag.ids)])
        post.write({'series_id': False})
        self.assertFalse(post.series_id)

    def test_explicit_position_is_kept(self):
        post = self._post(series_id=self.series.id, series_position=7)
        self.assertEqual(post.series_position, 7)

    def test_tag_is_unique_across_series(self):
        with mute_logger('odoo.sql_db'), self.assertRaises(IntegrityError):
            with self.env.cr.savepoint():
                self.Series.create({
                    'name': 'Doublon', 'blog_id': self.blog_dev.id, 'tag_id': self.tag.id})

    def test_two_series_without_tag_are_allowed(self):
        self.Series.create([
            {'name': 'Sans étiquette 1', 'blog_id': self.blog_dev.id},
            {'name': 'Sans étiquette 2', 'blog_id': self.blog_dev.id},
        ])

    def test_deleting_series_unlinks_posts(self):
        post = self._post(tag_ids=[(6, 0, self.tag.ids)])
        self.series.unlink()
        self.assertFalse(post.series_id)

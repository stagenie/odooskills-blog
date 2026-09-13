from lxml import etree

from odoo.exceptions import AccessError
from odoo.tests import TransactionCase, new_test_user, tagged


@tagged('post_install', '-at_install')
class TestBackendViews(TransactionCase):

    def _arch(self, model, xmlid, view_type):
        view_id = self.env.ref(xmlid).id if xmlid else None
        return etree.fromstring(self.env[model].get_view(view_id, view_type)['arch'])

    def test_post_form_has_series_tab(self):
        arch = self._arch('blog.post', 'website_blog.view_blog_post_form', 'form')
        page = arch.find(".//page[@name='oski_series']")
        self.assertIsNotNone(page)
        for name in ('series_id', 'series_position', 'series_block'):
            self.assertIsNotNone(page.find(".//field[@name='%s']" % name))

    def test_post_search_filters(self):
        arch = self._arch('blog.post', 'website_blog.view_blog_post_search', 'search')
        self.assertIsNotNone(arch.find(".//filter[@name='oski_no_series']"))
        self.assertIsNotNone(arch.find(".//filter[@name='oski_group_by_series']"))

    def test_post_list_has_series_column(self):
        arch = self._arch('blog.post', 'website_blog.view_blog_post_list', 'list')
        self.assertIsNotNone(arch.find(".//field[@name='series_id']"))

    def test_series_form_cannot_delete_posts_from_the_list(self):
        arch = self._arch('oski.blog.series', None, 'form')
        post_list = arch.find(".//field[@name='post_ids']/list")
        self.assertIsNotNone(post_list)
        self.assertEqual(post_list.get('delete'), '0')
        self.assertEqual(post_list.get('create'), '0')
        self.assertIsNotNone(post_list.find(".//field[@name='series_position'][@widget='handle']"))

    def test_menus_and_actions_exist(self):
        self.assertEqual(self.env.ref('oski_blog_series.action_oski_blog_series').res_model, 'oski.blog.series')
        self.assertEqual(self.env.ref('oski_blog_series.menu_oski_blog_series').parent_id,
                         self.env.ref('website_blog.menu_website_blog_root_global'))
        self.env.ref('oski_blog_series.menu_oski_blog_odoo_version')

    def test_access_rights(self):
        blog = self.env['blog.blog'].create({'name': 'Blog droits'})
        designer = new_test_user(self.env, login='oski_series_designer',
                                 groups='base.group_user,website.group_website_designer')
        employee = new_test_user(self.env, login='oski_series_employee', groups='base.group_user')
        public = self.env.ref('base.public_user')
        series = self.env['oski.blog.series'].with_user(designer).create(
            {'name': 'Par le concepteur', 'blog_id': blog.id})
        self.assertEqual(self.env['oski.blog.series'].with_user(public).search([('id', '=', series.id)]), series)
        with self.assertRaises(AccessError):
            self.env['oski.blog.series'].with_user(employee).create({'name': 'Refusée', 'blog_id': blog.id})

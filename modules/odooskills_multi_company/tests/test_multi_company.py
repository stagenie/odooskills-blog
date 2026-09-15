from datetime import timedelta

from odoo import fields
from odoo.exceptions import AccessError, UserError
from odoo.tests import Form, TransactionCase, new_test_user, tagged


@tagged('post_install', '-at_install')
class TestMultiCompany(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_a = cls.env['res.company'].create({'name': "Société A"})
        cls.company_b = cls.env['res.company'].create({'name': "Société B"})
        cls.user_a = new_test_user(
            cls.env, login='mc_user_a', groups='base.group_user',
            company_id=cls.company_a.id, company_ids=[cls.company_a.id],
        )
        cls.user_ab = new_test_user(
            cls.env, login='mc_user_ab', groups='base.group_user,base.group_multi_company',
            company_id=cls.company_a.id, company_ids=[cls.company_a.id, cls.company_b.id],
        )
        Site = cls.env['odooskills.work.site']
        cls.site_a = Site.create({'name': "Atelier A", 'company_id': cls.company_a.id})
        cls.site_b = Site.create({'name': "Atelier B", 'company_id': cls.company_b.id})
        cls.site_shared = Site.create({'name': "Site partagé"})
        cls.partner = cls.env['res.partner'].create({'name': "Client commun"})

    def _order(self, company, site, **vals):
        return self.env['odooskills.work.order'].create(
            dict(company_id=company.id, site_id=site.id, **vals))

    # 1. env.company / env.companies
    def test_env_company_follows_allowed_company_ids(self):
        env = self.env(user=self.user_ab, context={
            'allowed_company_ids': [self.company_b.id, self.company_a.id]})
        self.assertEqual(env.company, self.company_b)
        self.assertEqual(env.companies, self.company_b | self.company_a)

    def test_env_company_defaults_to_user_main_company(self):
        env = self.env(user=self.user_ab, context={})
        self.assertEqual(env.company, self.company_a)
        self.assertEqual(env.companies, self.company_a | self.company_b)

    def test_unauthorized_company_in_context_raises(self):
        env = self.env(user=self.user_a, context={'allowed_company_ids': [self.company_b.id]})
        with self.assertRaises(AccessError):
            env.company  # noqa: B018

    def test_sudo_skips_company_check(self):
        env = self.env(user=self.user_a, context={'allowed_company_ids': [self.company_b.id]}, su=True)
        self.assertEqual(env.company, self.company_b)

    # 2. ir.rule
    def test_record_rule_isolates_companies(self):
        order_a = self._order(self.company_a, self.site_a)
        order_b = self._order(self.company_b, self.site_b)
        Order = self.env['odooskills.work.order']
        mine = (order_a | order_b)
        seen_a = Order.with_user(self.user_a).search([('id', 'in', mine.ids)])
        self.assertEqual(seen_a, order_a)
        seen_ab_one = Order.with_user(self.user_ab).with_context(
            allowed_company_ids=[self.company_a.id]).search([('id', 'in', mine.ids)])
        self.assertEqual(seen_ab_one, order_a)
        seen_ab_all = Order.with_user(self.user_ab).with_context(
            allowed_company_ids=[self.company_a.id, self.company_b.id]).search([('id', 'in', mine.ids)])
        self.assertEqual(seen_ab_all, mine)

    def test_sudo_bypasses_record_rules(self):
        order_b = self._order(self.company_b, self.site_b)
        Order = self.env['odooskills.work.order'].with_user(self.user_a)
        self.assertFalse(Order.search([('id', '=', order_b.id)]))
        self.assertEqual(Order.sudo().search([('id', '=', order_b.id)]), order_b)

    # 3. _check_company_auto + check_company
    def test_check_company_blocks_crossover(self):
        with self.assertRaises(UserError) as cm:
            self._order(self.company_a, self.site_b)
        print("\nMESSAGE check_company:\n" + str(cm.exception))

    def test_shared_site_accepted_everywhere(self):
        self._order(self.company_a, self.site_shared)
        self._order(self.company_b, self.site_shared)

    def test_changing_company_later_is_checked_too(self):
        order = self._order(self.company_a, self.site_a)
        with self.assertRaises(UserError):
            order.company_id = self.company_b

    def test_field_domain_is_generated(self):
        domain = self.env['odooskills.work.order']._fields['site_id']._description_domain(self.env)
        print("\nDOMAINE site_id:", domain)
        self.assertIn("company_id", domain)

    # 4. company_dependent
    def test_company_dependent_value_per_company(self):
        self.partner.with_company(self.company_a).odooskills_hourly_rate = 50.0
        self.partner.with_company(self.company_b).odooskills_hourly_rate = 80.0
        self.assertEqual(self.partner.with_company(self.company_a).odooskills_hourly_rate, 50.0)
        self.assertEqual(self.partner.with_company(self.company_b).odooskills_hourly_rate, 80.0)
        self.env.flush_all()
        self.env.cr.execute(
            "SELECT odooskills_hourly_rate FROM res_partner WHERE id = %s", [self.partner.id])
        print("\nCOLONNE jsonb:", self.env.cr.fetchone()[0])

    def test_order_reads_rate_of_its_own_company(self):
        self.partner.with_company(self.company_a).odooskills_hourly_rate = 50.0
        self.partner.with_company(self.company_b).odooskills_hourly_rate = 80.0
        # l'utilisateur travaille dans A, le bon appartient à B
        env = self.env(user=self.user_ab, context={
            'allowed_company_ids': [self.company_a.id, self.company_b.id]})
        order = env['odooskills.work.order'].create({
            'company_id': self.company_b.id, 'site_id': self.site_b.id,
            'partner_id': self.partner.id})
        self.assertEqual(env.company, self.company_a)
        self.assertEqual(order.hourly_rate, 80.0)
        # sans with_company, on lit la valeur de la société active
        self.assertEqual(order.partner_id.odooskills_hourly_rate, 50.0)

    # 5. séquences
    def test_sequence_per_company(self):
        # sociétés neuves : leurs compteurs n'ont servi à aucun autre test
        year = fields.Date.today().year
        company_c, company_d = self.env['res.company'].create([{'name': "Société C"}, {'name': "Société D"}])
        c1 = self._order(company_c, self.site_shared)
        d1 = self._order(company_d, self.site_shared)
        c2 = self._order(company_c, self.site_shared)
        print("\nSEQUENCES:", c1.name, d1.name, c2.name)
        self.assertEqual(c1.name, f"BI/{year}/0001")
        self.assertEqual(d1.name, f"BI/{year}/0001")
        self.assertEqual(c2.name, f"BI/{year}/0002")

    def test_failed_create_still_consumes_a_number(self):
        year = fields.Date.today().year
        company_e = self.env['res.company'].create({'name': "Société E"})
        e1 = self._order(company_e, self.site_shared)
        with self.assertRaises(UserError):
            self._order(company_e, self.site_b)   # refusé par check_company
        e2 = self._order(company_e, self.site_shared)
        print("\nTROU:", e1.name, "->", e2.name)
        self.assertEqual(e1.name, f"BI/{year}/0001")
        self.assertEqual(e2.name, f"BI/{year}/0003")

    def test_new_company_gets_its_sequence(self):
        company_c = self.env['res.company'].create({'name': "Société C"})
        seq = self.env['ir.sequence'].search([
            ('code', '=', 'odooskills.work.order'), ('company_id', '=', company_c.id)])
        self.assertEqual(len(seq), 1)

    # 6. cron
    def test_cron_runs_as_root_with_main_company(self):
        cron = self.env.ref('odooskills_multi_company.cron_mark_late')
        cron_env = self.env(user=cron.user_id)
        print("\nCRON user:", cron.user_id.login, "su:", cron_env.su,
              "env.company:", cron_env.company.name)
        self.assertTrue(cron_env.su)

    def test_cron_processes_each_company(self):
        yesterday = fields.Date.today() - timedelta(days=1)
        order_a = self._order(self.company_a, self.site_a, date_deadline=yesterday)
        order_b = self._order(self.company_b, self.site_b, date_deadline=yesterday)
        self.env['odooskills.work.order']._cron_mark_late()
        self.assertEqual((order_a | order_b).mapped('state'), ['late', 'late'])

    # 7. la vue et le domaine généré
    def test_form_default_company_is_active_company(self):
        env = self.env(user=self.user_ab, context={
            'allowed_company_ids': [self.company_b.id, self.company_a.id]})
        form = Form(env['odooskills.work.order'])
        self.assertEqual(form.company_id, self.company_b)
        form.site_id = self.site_b
        order = form.save()
        self.assertEqual(order.company_id, self.company_b)

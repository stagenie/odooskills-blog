from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'adi_odooskills_crm_antispam')
class TestCrmAntispam(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Lead = cls.env['crm.lead']
        cls.Blacklist = cls.env['mail.blacklist']

    def _create_lead(self, email):
        return self.Lead.create({
            'name': f"Test lead {email}",
            'email_from': email,
        })

    def test_create_blacklisted_email_is_archived(self):
        self.Blacklist._add('spam@bad.example.com')
        lead = self._create_lead('Spam <spam@bad.example.com>')
        self.assertFalse(
            lead.active,
            "Lead with blacklisted email should be auto-archived on create",
        )

    def test_create_unknown_email_stays_active(self):
        lead = self._create_lead('legit@example.com')
        self.assertTrue(
            lead.active,
            "Lead from a clean email must remain active",
        )

    def test_create_no_email_stays_active(self):
        lead = self.Lead.create({'name': 'Lead without email'})
        self.assertTrue(lead.active)

    def test_mark_as_spam_blacklists_and_archives(self):
        lead = self._create_lead('bot@spam-domain.example')
        self.assertTrue(lead.active)

        result = lead.action_mark_as_spam()

        self.assertFalse(lead.active, "Lead must be archived after SPAM action")
        bl = self.Blacklist.search([('email', '=', 'bot@spam-domain.example')])
        self.assertEqual(len(bl), 1)
        self.assertTrue(bl.active)
        self.assertEqual(result['type'], 'ir.actions.client')

    def test_mark_as_spam_archives_siblings(self):
        l1 = self._create_lead('floods@bot.example')
        l2 = self._create_lead('FLOODS@bot.example')
        l3 = self._create_lead('Spammer <floods@bot.example>')
        self.assertTrue(all(l.active for l in (l1, l2, l3)))

        l1.action_mark_as_spam()

        for l in (l1, l2, l3):
            l.invalidate_recordset(['active'])
        self.assertFalse(l1.active)
        self.assertFalse(l2.active, "Sibling lead must be archived too")
        self.assertFalse(l3.active, "Sibling lead must be archived too")

    def test_mark_as_spam_handles_existing_archived_blacklist(self):
        self.Blacklist._add('twice@bot.example')
        bl = self.Blacklist.search([('email', '=', 'twice@bot.example')])
        bl.action_archive()
        self.assertFalse(bl.active)

        lead = self._create_lead('twice@bot.example')
        lead.action_mark_as_spam()

        bl.invalidate_recordset(['active'])
        self.assertTrue(bl.active, "Existing blacklist entry must be re-activated")

    def test_mark_as_spam_no_email_does_not_crash(self):
        lead = self.Lead.create({'name': 'Lead without email'})
        result = lead.action_mark_as_spam()
        self.assertFalse(lead.active)
        self.assertEqual(result['type'], 'ir.actions.client')

    def test_create_multi_partial_blacklist(self):
        self.Blacklist._add('blocked@bot.example')
        leads = self.Lead.create([
            {'name': 'OK', 'email_from': 'ok@example.com'},
            {'name': 'KO', 'email_from': 'blocked@bot.example'},
            {'name': 'OK2', 'email_from': 'fine@example.com'},
        ])
        self.assertTrue(leads[0].active)
        self.assertFalse(leads[1].active)
        self.assertTrue(leads[2].active)

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestWelcomeMail(TransactionCase):
    def test_mail_sent_on_new_offer(self):
        Offer = self.env['oski.welcome.offer']
        p = self.env['res.partner'].create({'name': 'M', 'email': 'mail1@example.com'})
        before = self.env['mail.mail'].search_count([])
        Offer.create_for_email('mail1@example.com', p, 'popup')
        after = self.env['mail.mail'].search_count([])
        self.assertEqual(after, before + 1)

    def test_no_mail_on_duplicate(self):
        Offer = self.env['oski.welcome.offer']
        p = self.env['res.partner'].create({'name': 'M', 'email': 'mail2@example.com'})
        Offer.create_for_email('mail2@example.com', p, 'popup')
        before = self.env['mail.mail'].search_count([])
        Offer.create_for_email('mail2@example.com', p, 'popup')
        after = self.env['mail.mail'].search_count([])
        self.assertEqual(after, before)

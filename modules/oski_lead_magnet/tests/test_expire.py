from datetime import timedelta

from odoo import fields
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestExpire(TransactionCase):
    def test_cron_expires_past_deadline(self):
        Offer = self.env['oski.welcome.offer']
        p = self.env['res.partner'].create({'name': 'E', 'email': 'exp1@example.com'})
        offer = Offer.create_for_email('exp1@example.com', p, 'popup')
        offer.activate()
        offer.deadline = fields.Datetime.now() - timedelta(hours=1)
        Offer._cron_expire()
        self.assertEqual(offer.state, 'expired')

    def test_cron_keeps_live_offer(self):
        Offer = self.env['oski.welcome.offer']
        p = self.env['res.partner'].create({'name': 'E', 'email': 'exp2@example.com'})
        offer = Offer.create_for_email('exp2@example.com', p, 'popup')
        offer.activate()
        Offer._cron_expire()
        self.assertEqual(offer.state, 'active')

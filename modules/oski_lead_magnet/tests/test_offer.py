from datetime import timedelta
from unittest.mock import patch

from odoo import fields
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestOffer(TransactionCase):
    def _make_partner(self, email):
        return self.env['res.partner'].create({'name': email, 'email': email})

    def test_create_generates_dormant_offer_with_coupon(self):
        Offer = self.env['oski.welcome.offer']
        p = self._make_partner('new1@example.com')
        offer = Offer.create_for_email('new1@example.com', p, 'popup')
        self.assertEqual(offer.state, 'dormant')
        self.assertTrue(offer.token)
        self.assertTrue(offer.coupon_id)
        self.assertFalse(offer.deadline)

    def test_create_is_idempotent_per_email(self):
        Offer = self.env['oski.welcome.offer']
        p = self._make_partner('dup@example.com')
        o1 = Offer.create_for_email('dup@example.com', p, 'popup')
        o2 = Offer.create_for_email('dup@example.com', p, 'pdf:x')
        self.assertEqual(o1, o2)
        self.assertEqual(Offer.search_count([('email', '=', 'dup@example.com')]), 1)

    def test_activate_sets_deadline_72h(self):
        Offer = self.env['oski.welcome.offer']
        p = self._make_partner('act@example.com')
        offer = Offer.create_for_email('act@example.com', p, 'popup')
        offer.activate()
        self.assertEqual(offer.state, 'active')
        self.assertTrue(offer.deadline)
        delta = offer.deadline - offer.activated_at
        self.assertAlmostEqual(delta.total_seconds(), 72 * 3600, delta=120)

    def test_activate_is_idempotent(self):
        Offer = self.env['oski.welcome.offer']
        p = self._make_partner('act2@example.com')
        offer = Offer.create_for_email('act2@example.com', p, 'popup')
        offer.activate()
        first_deadline = offer.deadline
        offer.activate()
        self.assertEqual(offer.deadline, first_deadline)

    def test_create_recovers_from_race(self):
        """A concurrent request already inserted the row, but our existence
        check missed it (race window) — create_for_email must recover via
        the savepoint/IntegrityError guard and return the existing offer,
        not raise and not create a duplicate row."""
        Offer = self.env['oski.welcome.offer']
        p = self._make_partner('race@example.com')
        first = Offer.create_for_email('race@example.com', p, 'popup')

        real_search = type(Offer).search
        missed = {'done': False}

        def flaky_search(self2, domain, *args, **kwargs):
            # Only spoof the very first lookup-by-email (the existence
            # check in create_for_email); leave every other search
            # (including our own recovery search) untouched.
            if not missed['done'] and domain == [('email', '=', 'race@example.com')]:
                missed['done'] = True
                return self2.browse()
            return real_search(self2, domain, *args, **kwargs)

        with patch.object(type(Offer), 'search', flaky_search):
            second = Offer.create_for_email('race@example.com', p, 'popup')

        self.assertEqual(second, first)
        self.assertEqual(Offer.search_count([('email', '=', 'race@example.com')]), 1)

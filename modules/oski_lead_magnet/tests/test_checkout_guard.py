from datetime import timedelta

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestCheckoutGuard(TransactionCase):
    def test_confirm_blocked_when_offer_expired(self):
        Offer = self.env['oski.welcome.offer']
        partner = self.env['res.partner'].create({'name': 'B', 'email': 'guard@example.com'})
        offer = Offer.create_for_email('guard@example.com', partner, 'popup')
        offer.activate()
        offer.write({'state': 'expired',
                     'deadline': fields.Datetime.now() - timedelta(hours=1)})
        product = self.env['product.product'].create({'name': 'Ebook', 'list_price': 20})
        order = self.env['sale.order'].create({
            'partner_id': partner.id,
            'order_line': [(0, 0, {'product_id': product.id, 'product_uom_qty': 1})],
        })
        # simule l'application du coupon expiré
        order.applied_coupon_ids = [(4, offer.coupon_id.id)]
        with self.assertRaises(UserError):
            order._action_confirm()

    def test_confirm_marks_offer_used_when_coupon_valid(self):
        Offer = self.env['oski.welcome.offer']
        partner = self.env['res.partner'].create({'name': 'V', 'email': 'valid@example.com'})
        offer = Offer.create_for_email('valid@example.com', partner, 'popup')
        offer.activate()
        product = self.env['product.product'].create({'name': 'Ebook', 'list_price': 20})
        order = self.env['sale.order'].create({
            'partner_id': partner.id,
            'order_line': [(0, 0, {'product_id': product.id, 'product_uom_qty': 1})],
        })
        # simule l'application du coupon valide (non expiré)
        order.applied_coupon_ids = [(4, offer.coupon_id.id)]
        order._action_confirm()
        self.assertEqual(offer.state, 'used')

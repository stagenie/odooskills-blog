"""Tests du wizard de clôture helpdesk.ticket.close.wizard.

Couvre : valeurs par défaut, clôture simple, clôture bulk.
Utilise odoo.tests.Form pour simuler l'interaction UI.
"""
from odoo.tests import tagged, Form

from .common import HelpdeskCommon


@tagged('post_install', '-at_install')
class TestCloseWizard(HelpdeskCommon):
    """Tests de helpdesk.ticket.close.wizard (TransientModel)."""

    def _make_ticket(self, name='Ticket Wizard Test', **kwargs):
        """Fabrique un ticket de test sans envoi de mail."""
        defaults = {
            'name': name,
            'partner_id': self.partner_customer.id,
        }
        defaults.update(kwargs)
        return self.env['helpdesk.ticket'].with_context(skip_mail=True).create(defaults)

    # ── 1. Valeurs par défaut ─────────────────────────────────────────────

    def test_wizard_default_values(self):
        """Le wizard pré-remplit ticket_id via active_id et resolution_reason via default."""
        ticket = self._make_ticket()

        wizard_form = Form(
            self.env['helpdesk.ticket.close.wizard'].with_context(
                active_id=ticket.id,
                active_model='helpdesk.ticket',
            )
        )

        # ticket_id doit être pré-rempli via default_get
        self.assertEqual(wizard_form.ticket_id, ticket,
                         "ticket_id doit être pré-rempli via active_id.")
        # resolution_reason a une valeur default='resolved'
        self.assertEqual(wizard_form.resolution_reason, 'resolved',
                         "resolution_reason doit être 'resolved' par défaut.")

    # ── 2. Clôture simple ─────────────────────────────────────────────────

    def test_wizard_save_and_apply(self):
        """Saisir les champs dans le Form puis action_close() -> ticket en done + chatter."""
        ticket = self._make_ticket()
        msg_count_before = len(ticket.message_ids)

        wizard_form = Form(
            self.env['helpdesk.ticket.close.wizard'].with_context(
                active_id=ticket.id,
                active_model='helpdesk.ticket',
            )
        )
        wizard_form.resolution_reason = 'resolved'
        wizard_form.resolution_note = 'Problème résolu lors du test.'
        wizard_form.hours_spent = 2.5
        wizard_form.notify_partner = True

        wizard = wizard_form.save()
        wizard.action_close()

        self.env.flush_all()
        self.env.invalidate_all()

        self.assertEqual(ticket.state, 'done',
                         "Le ticket doit être en état 'done' après action_close().")
        self.assertGreater(
            len(ticket.message_ids), msg_count_before,
            "Un message doit avoir été posté dans le chatter après clôture.",
        )
        # La note de résolution est écrite sur le ticket
        self.assertIn('Problème résolu lors du test.', ticket.resolution_note or '',
                      "La note de résolution doit être reportée sur le ticket.")

    # ── 3. Clôture bulk ───────────────────────────────────────────────────

    def test_wizard_bulk_close_three_tickets(self):
        """Appeler action_close() sur 3 tickets en boucle -> tous en done."""
        tickets = self.env['helpdesk.ticket'].with_context(skip_mail=True).create([
            {'name': 'Bulk 1', 'partner_id': self.partner_customer.id},
            {'name': 'Bulk 2', 'partner_id': self.partner_customer.id},
            {'name': 'Bulk 3', 'partner_id': self.partner_customer.id},
        ])

        for ticket in tickets:
            wizard = self.env['helpdesk.ticket.close.wizard'].with_context(
                active_id=ticket.id,
                active_model='helpdesk.ticket',
            ).create({
                'ticket_id': ticket.id,
                'resolution_reason': 'resolved',
            })
            wizard.action_close()

        self.env.flush_all()
        self.env.invalidate_all()

        for ticket in tickets:
            self.assertEqual(
                ticket.state, 'done',
                f"Le ticket {ticket.name} doit être en état 'done'.",
            )

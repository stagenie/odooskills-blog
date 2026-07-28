from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestNewsletterGlobal(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.globale = cls.env.ref('mass_mailing.mailing_list_data')
        cls.segment = cls.env['mailing.list'].create({'name': 'Segment de test'})

    def _subscription(self, contact, mailing_list):
        return self.env['mailing.subscription'].search([
            ('contact_id', '=', contact.id),
            ('list_id', '=', mailing_list.id),
        ])

    def test_new_contact_joins_global_list(self):
        contact = self.env['mailing.contact'].create({
            'name': 'Nouveau', 'email': 'nouveau@example.com'})
        self.assertIn(self.globale, contact.list_ids)

    def test_new_contact_created_on_segment_joins_global_list(self):
        """La porte d'entrée popup/PDF pousse vers un segment, pas la Globale."""
        contact = self.env['mailing.contact'].create({
            'name': 'Prospect', 'email': 'prospect@example.com',
            'list_ids': [(4, self.segment.id)]})
        self.assertIn(self.segment, contact.list_ids)
        self.assertIn(self.globale, contact.list_ids)

    def test_existing_contact_added_to_segment_joins_global_list(self):
        contact = self.env['mailing.contact'].create({
            'name': 'Ancien', 'email': 'ancien@example.com'})
        self._subscription(contact, self.globale).unlink()
        self.assertNotIn(self.globale, contact.list_ids)

        contact.write({'list_ids': [(4, self.segment.id)]})
        self.assertIn(self.globale, contact.list_ids)

    def test_optout_is_not_resurrected(self):
        """Une désinscription de la Globale survit à une inscription à un segment."""
        contact = self.env['mailing.contact'].create({
            'name': 'Parti', 'email': 'parti@example.com'})
        subscription = self._subscription(contact, self.globale)
        subscription.opt_out = True

        contact.write({'list_ids': [(4, self.segment.id)]})

        subscription = self._subscription(contact, self.globale)
        self.assertEqual(len(subscription), 1, "aucune souscription en double")
        self.assertTrue(subscription.opt_out, "l'opt_out doit être préservé")

    def test_removal_from_global_list_is_undone(self):
        """Sortir quelqu'un de la Globale n'est pas un geste prévu.

        Le référentiel doit rester complet : pour ne plus écrire à quelqu'un on
        pose opt_out (ou la liste noire), on ne le retire pas de la liste.
        """
        contact = self.env['mailing.contact'].create({
            'name': 'Retire', 'email': 'retire@example.com'})
        contact.write({'list_ids': [(3, self.globale.id)]})
        self.assertIn(self.globale, contact.list_ids)

    def test_ensure_is_idempotent(self):
        contact = self.env['mailing.contact'].create({
            'name': 'Idem', 'email': 'idem@example.com'})
        contact._oski_ensure_global_list()
        contact._oski_ensure_global_list()
        self.assertEqual(len(self._subscription(contact, self.globale)), 1)

    def test_backfill_covers_orphan_contact(self):
        from ..hooks import post_init
        contact = self.env['mailing.contact'].create({
            'name': 'Orphelin', 'email': 'orphelin@example.com'})
        self._subscription(contact, self.globale).unlink()

        post_init(self.env)

        self.assertIn(self.globale, contact.list_ids)

from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged

from .test_inbox_routing import process_raw


@tagged('post_install', '-at_install')
class TestDraft(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.box_a = cls.env['oski.mailbox'].create({
            'name': 'Support', 'email': 'support@odooskills.example',
            'imap_host': 'imap.test.local', 'imap_user': 'a',
            'imap_password': 'fake-test-password',
            'signature': '<p>Support — OdooSkills</p>',
        })
        cls.box_b = cls.env['oski.mailbox'].create({
            'name': 'Ventes', 'email': 'ventes@odooskills.example',
            'imap_host': 'imap.test.local', 'imap_user': 'b',
            'imap_password': 'fake-test-password',
            'signature': '<p>Ventes — OdooSkills</p>',
        })
        rec_id = process_raw(cls.env, cls.box_a.fetchmail_server_id,
                             msg_id='<t-draft-1@example.com>')
        cls.record = cls.env['oski.mail.inbox'].browse(rec_id)

    def _draft(self, **overrides):
        values = {
            'mailbox_id': self.box_a.id,
            'email_to': 'client@example.com',
            'subject': 'Réponse',
            'body_html': '<p>Bonjour</p>',
        }
        values.update(overrides)
        return self.env['oski.mail.draft'].create(values)

    # -- expéditeur --------------------------------------------------------
    def test_send_uses_chosen_mailbox_not_record_mailbox(self):
        draft = self._draft(mailbox_id=self.box_b.id, inbox_id=self.record.id)
        draft.action_send()
        message = draft.mail_message_id
        self.assertIn('ventes@odooskills.example', message.email_from,
                      "l'expéditeur choisi doit primer sur la boîte de l'email reçu")

    def test_reply_to_follows_chosen_mailbox(self):
        draft = self._draft(mailbox_id=self.box_b.id, inbox_id=self.record.id)
        draft.action_send()
        self.assertIn('ventes@odooskills.example', draft.mail_message_id.reply_to)

    def test_reply_to_defaults_to_record_mailbox(self):
        reply_to = self.record._notify_get_reply_to()
        self.assertIn('support@odooskills.example', reply_to[self.record.id],
                      "hors contexte d'envoi, la boîte de la fiche reste la référence")

    def test_mail_server_reaches_the_message(self):
        server = self.env['ir.mail_server'].create({
            'name': 'Test SMTP', 'smtp_host': 'smtp.test.local', 'smtp_port': 587})
        self.box_b.mail_server_id = server
        draft = self._draft(mailbox_id=self.box_b.id, inbox_id=self.record.id)
        draft.action_send()
        self.assertEqual(draft.mail_message_id.mail_server_id, server)

    def test_recipients_do_not_create_partners(self):
        before = self.env['res.partner'].search_count([])
        draft = self._draft(email_to='inconnu-total@example.com',
                            inbox_id=self.record.id)
        draft.action_send()
        self.assertEqual(self.env['res.partner'].search_count([]), before,
                         "outgoing_email_to évite de créer un partenaire par destinataire")
        self.assertIn('inconnu-total@example.com',
                      draft.mail_message_id.outgoing_email_to)

    # -- signature ---------------------------------------------------------
    def test_reply_body_carries_signature_and_quote(self):
        body = self.record._reply_body()
        self.assertIn('Support — OdooSkills', body)
        self.assertIn('data-oski-signature', body)
        self.assertIn('message de test', body, "l'original doit être cité")

    def test_changing_mailbox_swaps_signature_once(self):
        draft = self._draft(body_html=self.record._reply_body())
        draft.mailbox_id = self.box_b
        draft._onchange_mailbox_signature()
        self.assertIn('Ventes — OdooSkills', draft.body_html)
        self.assertNotIn('Support — OdooSkills', draft.body_html)
        self.assertEqual(draft.body_html.count('data-oski-signature'), 1,
                         "changer d'expéditeur ne doit pas empiler les signatures")

    def test_signature_containing_a_div_is_removed_whole(self):
        # une expression régulière non gourmande couperait au premier </div>
        # et laisserait la moitié de l'ancienne signature dans le corps
        self.box_a.signature = '<div><p>Bureau Support</p><div>Sous-titre</div></div>'
        draft = self._draft(body_html=self.record._reply_body())
        draft.mailbox_id = self.box_b
        draft._onchange_mailbox_signature()
        self.assertNotIn('Bureau Support', draft.body_html)
        self.assertNotIn('Sous-titre', draft.body_html)
        self.assertIn('Ventes — OdooSkills', draft.body_html)
        self.assertEqual(draft.body_html.count('data-oski-signature'), 1)

    def test_falls_back_on_user_signature(self):
        self.box_a.signature = False
        self.env.user.signature = '<p>Signature personnelle</p>'
        draft = self._draft()
        self.assertIn('Signature personnelle',
                      draft._signature_block(self.box_a))

    def test_no_signature_no_block(self):
        self.box_a.signature = False
        self.env.user.signature = False
        self.assertEqual(str(self._draft()._signature_block(self.box_a)), '')

    def test_body_sent_verbatim(self):
        draft = self._draft(body_html='<p>Corps exact du message.</p>',
                            inbox_id=self.record.id)
        draft.action_send()
        body = draft.mail_message_id.body
        self.assertIn('Corps exact du message.', body)
        self.assertNotIn('Votre Email reçu', body,
                         "aucune couche de notification ne doit polluer le corps")
        self.assertNotIn('utm_source=db', body)

    # -- pièces jointes et cycle de vie ------------------------------------
    def test_attachments_follow_the_message(self):
        attachment = self.env['ir.attachment'].create({
            'name': 'devis.pdf', 'datas': 'JVBERi0=', 'mimetype': 'application/pdf'})
        draft = self._draft(attachment_ids=[(6, 0, attachment.ids)],
                            inbox_id=self.record.id)
        draft.action_send()
        self.assertIn(attachment, draft.mail_message_id.attachment_ids)

    def test_new_message_creates_its_thread(self):
        draft = self._draft(subject='Prise de contact')
        draft.action_send()
        self.assertTrue(draft.inbox_id,
                        "un message neuf doit avoir une fiche pour porter le fil")
        self.assertEqual(draft.inbox_id.state, 'answered')
        self.assertEqual(draft.inbox_id.mailbox_id, self.box_a)

    def test_sent_draft_is_locked(self):
        draft = self._draft(inbox_id=self.record.id)
        draft.action_send()
        self.assertEqual(draft.state, 'sent')
        with self.assertRaises(UserError):
            draft.write({'subject': 'Réécriture après coup'})

    def test_sending_twice_is_refused(self):
        draft = self._draft(inbox_id=self.record.id)
        draft.action_send()
        with self.assertRaises(UserError):
            draft.action_send()

    def test_reply_marks_record_answered(self):
        self.record.state = 'new'
        draft = self._draft(inbox_id=self.record.id)
        draft.action_send()
        self.assertEqual(self.record.state, 'answered')


@tagged('post_install', '-at_install')
class TestDraftIsolation(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.box = cls.env['oski.mailbox'].create({
            'name': 'Support', 'email': 'iso@odooskills.example'})
        cls.alice = cls.env['res.users'].create({
            'name': 'Alice', 'login': 'draft_alice',
            'group_ids': [(6, 0, [
                cls.env.ref('base.group_user').id,
                cls.env.ref('oski_mail_inbox.group_user').id])],
        })
        cls.bob = cls.env['res.users'].create({
            'name': 'Bob', 'login': 'draft_bob',
            'group_ids': [(6, 0, [
                cls.env.ref('base.group_user').id,
                cls.env.ref('oski_mail_inbox.group_user').id])],
        })
        cls.chief = cls.env['res.users'].create({
            'name': 'Chef', 'login': 'draft_chief',
            'group_ids': [(6, 0, [
                cls.env.ref('base.group_user').id,
                cls.env.ref('oski_mail_inbox.group_manager').id])],
        })

    def _draft_for(self, user):
        return self.env['oski.mail.draft'].with_user(user).create({
            'mailbox_id': self.box.id, 'email_to': 'x@example.com',
            'subject': 'Privé', 'body_html': '<p>.</p>'})

    def test_user_sees_only_own_drafts(self):
        mine = self._draft_for(self.alice)
        other = self._draft_for(self.bob)
        visible = self.env['oski.mail.draft'].with_user(self.alice).search([])
        self.assertIn(mine, visible)
        self.assertNotIn(other, visible,
                         "un brouillon est un écrit privé tant qu'il n'est pas envoyé")

    def test_manager_sees_every_draft(self):
        mine = self._draft_for(self.alice)
        other = self._draft_for(self.bob)
        visible = self.env['oski.mail.draft'].with_user(self.chief).search([])
        self.assertIn(mine, visible)
        self.assertIn(other, visible)

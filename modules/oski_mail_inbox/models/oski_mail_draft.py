from lxml import html as lxml_html
from markupsafe import Markup

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import email_split, format_datetime, formataddr

SIGNATURE_ATTRIBUTE = 'data-oski-signature'


class OskiMailDraft(models.Model):
    _name = 'oski.mail.draft'
    _description = 'Brouillon de message'
    _order = 'write_date desc, id desc'
    _rec_name = 'subject'

    mailbox_id = fields.Many2one(
        'oski.mailbox', string='Envoyer depuis', required=True,
        default=lambda self: self.env['oski.mailbox'].search([], limit=1))
    inbox_id = fields.Many2one(
        'oski.mail.inbox', string='En réponse à', ondelete='set null', readonly=True)
    email_to = fields.Char(string='À', required=True)
    email_cc = fields.Char(string='Copie')
    subject = fields.Char(string='Sujet', required=True)
    # sanitize_attributes=False : le sanitizer HTML par défaut de l'ORM ne
    # garde qu'une liste blanche d'attributs qui n'inclut pas
    # data-oski-signature, ce qui effacerait le marqueur de signature à
    # chaque écriture. Le désactiver ne réintroduit pas de danger : les
    # balises restent filtrées (sanitize_tags reste actif), seule la liste
    # blanche d'attributs s'élargit — c'est le même compromis que celui du
    # corps natif de mail.message pour ses propres marqueurs data-o-mail-*.
    body_html = fields.Html(string='Message', sanitize=True, sanitize_attributes=False)
    attachment_ids = fields.Many2many('ir.attachment', string='Pièces jointes')
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('sent', 'Envoyé'),
    ], string='État', default='draft', readonly=True, index=True)
    date_sent = fields.Datetime(string='Envoyé le', readonly=True)
    mail_message_id = fields.Many2one(
        'mail.message', string='Message produit', readonly=True, ondelete='set null')

    def write(self, vals):
        if set(vals) - {'state', 'date_sent', 'mail_message_id', 'inbox_id'}:
            for draft in self:
                if draft.state == 'sent':
                    raise UserError(_(
                        "Ce message a été envoyé le %s : il ne peut plus être modifié.",
                        format_datetime(self.env, draft.date_sent)))
        return super().write(vals)

    # ------------------------------------------------------------------
    # Signature
    # ------------------------------------------------------------------
    @api.model
    def _signature_block(self, mailbox):
        """Bloc de signature marqué, prêt à être inséré dans un corps."""
        raw = (mailbox.signature or '').strip() or (self.env.user.signature or '').strip()
        if not raw:
            return Markup()
        return Markup('<div %s="1">%s</div>') % (
            Markup(SIGNATURE_ATTRIBUTE), Markup(raw))

    @api.model
    def _strip_signature(self, body):
        """Retire le bloc de signature d'un corps, quel que soit son contenu.

        lxml et non une expression régulière : une signature contenant un
        <div> ferait dérailler tout motif non gourmand, et couperait le corps
        au mauvais endroit."""
        if not body:
            return ''
        fragment = lxml_html.fragment_fromstring(body, create_parent='div')
        for node in fragment.xpath('//*[@%s]' % SIGNATURE_ATTRIBUTE):
            node.getparent().remove(node)
        rebuilt = fragment.text or ''
        rebuilt += ''.join(
            lxml_html.tostring(child, encoding='unicode') for child in fragment)
        return rebuilt

    @api.onchange('mailbox_id')
    def _onchange_mailbox_signature(self):
        for draft in self:
            stripped = draft._strip_signature(draft.body_html)
            draft.body_html = draft._signature_block(draft.mailbox_id) + Markup(stripped)

    # ------------------------------------------------------------------
    # Envoi
    # ------------------------------------------------------------------
    def _ensure_thread(self):
        """Retourne la fiche qui porte le fil ; un message neuf en crée une.

        Faire porter le fil par une fiche d'email plutôt que par le brouillon
        permet à la réponse du destinataire de rejoindre la conversation par
        In-Reply-To, au lieu d'ouvrir un fil orphelin."""
        self.ensure_one()
        if self.inbox_id:
            return self.inbox_id
        record = self.env['oski.mail.inbox'].create({
            'subject': self.subject,
            'email_from': self.mailbox_id.email,
            'mailbox_id': self.mailbox_id.id,
            'body_html': self.body_html,
            'date_received': fields.Datetime.now(),
            'state': 'answered',
        })
        self.inbox_id = record
        return record

    def _outgoing_emails(self):
        self.ensure_one()
        addresses = email_split(self.email_to or '') + email_split(self.email_cc or '')
        return ','.join(dict.fromkeys(addresses))

    def action_send(self):
        self.ensure_one()
        if self.state == 'sent':
            raise UserError(_("Ce message a déjà été envoyé."))
        mailbox = self.mailbox_id
        recipients = self._outgoing_emails()
        if not recipients:
            raise UserError(_("Aucun destinataire valide."))

        thread = self._ensure_thread()
        message = thread.with_context(oski_reply_mailbox_id=mailbox.id).message_post(
            body=Markup(self.body_html or ''),
            subject=self.subject,
            message_type='comment',
            subtype_xmlid='mail.mt_comment',
            email_from=formataddr((self.env.user.name, mailbox.email)),
            author_id=self.env.user.partner_id.id,
            outgoing_email_to=recipients,
            attachment_ids=self.attachment_ids.ids,
            mail_server_id=mailbox.mail_server_id.id or False,
        )
        self.write({
            'state': 'sent',
            'date_sent': fields.Datetime.now(),
            'mail_message_id': message.id,
        })
        return {'type': 'ir.actions.act_window_close'}

    def action_open_original(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'oski.mail.inbox',
            'view_mode': 'form',
            'res_id': self.inbox_id.id,
        }

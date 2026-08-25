import logging

from markupsafe import Markup

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import email_normalize, format_datetime, formataddr

_logger = logging.getLogger(__name__)


class OskiMailInbox(models.Model):
    _name = 'oski.mail.inbox'
    _description = 'Email reçu'
    _inherit = ['mail.thread']
    _order = 'date_received desc, id desc'
    _rec_name = 'subject'

    subject = fields.Char(string='Sujet')
    email_from = fields.Char(string='De', index=True)
    partner_id = fields.Many2one('res.partner', string='Contact')
    body_html = fields.Html(string='Message', sanitize=True)
    attachment_ids = fields.One2many(
        'ir.attachment', 'res_id', string='Pièces jointes',
        domain=[('res_model', '=', 'oski.mail.inbox')],
        help="Déposées par la passerelle entrante ; rien de neuf n'est stocké ici.")
    mailbox_id = fields.Many2one(
        'oski.mailbox', string='Boîte', index=True, ondelete='set null')
    date_received = fields.Datetime(
        string='Reçu le', default=fields.Datetime.now, index=True)
    active = fields.Boolean(default=True)
    email_message_id = fields.Char(
        string='Identifiant du message', index=True, copy=False,
        help="En-tête Message-ID de l'email d'origine. Seule clé stable pour "
             "retrouver ce message sur le serveur : un UID IMAP change dès que "
             "le message est déplacé.")
    state = fields.Selection([
        ('new', 'Nouveau'),
        ('answered', 'Répondu'),
        ('done', 'Clos'),
        ('spam', 'Indésirable'),
    ], string='État', default='new', index=True, tracking=True)
    imap_action_ids = fields.One2many(
        'oski.mail.imap.action', 'inbox_id', string='Actions distantes')
    imap_pending = fields.Boolean(
        string='Synchronisation en attente', compute='_compute_imap_pending', store=True)
    imap_failed = fields.Boolean(
        string='Synchronisation en échec', compute='_compute_imap_pending', store=True)

    @api.model
    def message_new(self, msg_dict, custom_values=None):
        mailbox = self.env['oski.mailbox']
        server_id = self.env.context.get('default_fetchmail_server_id')
        if server_id:
            mailbox = mailbox.sudo().search(
                [('fetchmail_server_id', '=', server_id)], limit=1)
        if not mailbox:
            # Fallback : rattache par adresse destinataire (mail arrivé hors
            # contexte fetchmail, ou serveur non lié à une boîte).
            recipients = ' '.join(filter(None, (
                msg_dict.get('to'), msg_dict.get('cc'),
                msg_dict.get('recipients')))).lower()
            for box in self.env['oski.mailbox'].sudo().search([]):
                if box.email and box.email.lower() in recipients:
                    mailbox = box
                    break
        email_from = msg_dict.get('email_from') or ''
        partner = self.env['res.partner']
        normalized = email_normalize(email_from)
        if normalized:
            found = self._mail_find_partner_from_emails([normalized])
            if found and found[0]:
                partner = found[0]
        values = {
            'subject': msg_dict.get('subject') or _('(sans sujet)'),
            'email_from': email_from,
            'partner_id': partner.id if partner else False,
            'body_html': msg_dict.get('body') or '',
            'mailbox_id': mailbox.id,
            'date_received': msg_dict.get('date') or fields.Datetime.now(),
            'state': 'new',
            'email_message_id': msg_dict.get('message_id') or False,
        }
        if custom_values:
            values.update(custom_values)
        record = super().message_new(msg_dict, custom_values=values)
        if self.env['oski.mail.blocklist']._is_blocked(email_from):
            record.write({'state': 'spam', 'active': False})
            # immediate=False : la relève ne doit pas dépendre d'une connexion
            # IMAP sortante ; le cron s'en charge quelques minutes plus tard.
            # notify_missing_id=False : voir _oski_imap_dispatch.
            record._oski_imap_dispatch('junk', immediate=False, notify_missing_id=False)
        return record

    def message_update(self, msg_dict, update_vals=None):
        vals = dict(update_vals or {})
        vals['date_received'] = msg_dict.get('date') or fields.Datetime.now()
        blocked = self.env['oski.mail.blocklist']._is_blocked(msg_dict.get('email_from'))
        if self.state != 'spam' and not blocked:
            # Une relance ranime le fil : on le sort d'archive et on le
            # remet en Nouveau. Un fil marqué indésirable reste indésirable
            # et archivé : c'est tout le sens du marquage, la routing ne
            # doit pas le ramener en tête de boîte.
            vals['state'] = 'new'
            vals['active'] = True
        elif blocked:
            # L'expéditeur a été bloqué depuis le dernier message de ce fil :
            # une relance ne doit pas ramener une fiche non-spam en tête de
            # boîte sous prétexte qu'elle existait déjà avant le blocage.
            vals['state'] = 'spam'
            vals['active'] = False
        if not self.email_message_id and msg_dict.get('message_id'):
            vals['email_message_id'] = msg_dict['message_id']
        result = super().message_update(msg_dict, update_vals=vals)
        if blocked:
            # immediate=False : la relève ne doit pas dépendre d'une connexion
            # IMAP sortante ; le cron s'en charge quelques minutes plus tard.
            self._oski_imap_dispatch('junk', immediate=False, notify_missing_id=False)
        return result

    def message_post(self, **kwargs):
        if (len(self) == 1 and self.mailbox_id.email
                and not kwargs.get('email_from')
                and kwargs.get('message_type') == 'comment'):
            kwargs['email_from'] = formataddr(
                (self.env.user.name, self.mailbox_id.email))
        message = super().message_post(**kwargs)
        if (message.message_type == 'comment'
                and not message.subtype_id.internal
                and self.env.user._is_internal()
                and self.state == 'new'):
            self.state = 'answered'
        return message

    def _notify_get_reply_to(self, default=None, author_id=False):
        result = super()._notify_get_reply_to(default=default, author_id=author_id)
        forced_id = self.env.context.get('oski_reply_mailbox_id')
        forced = self.env['oski.mailbox'].browse(forced_id).exists() if forced_id else None
        for record in self:
            mailbox = forced or record.mailbox_id
            if mailbox and mailbox.email:
                result[record.id] = formataddr(
                    (mailbox.name or mailbox.email, mailbox.email))
        return result

    @api.depends('imap_action_ids.state')
    def _compute_imap_pending(self):
        for record in self:
            record.imap_pending = any(
                action.state == 'pending' for action in record.imap_action_ids)
            record.imap_failed = any(
                action.state == 'failed' for action in record.imap_action_ids)

    def _oski_imap_dispatch(self, operation, immediate=True, notify_missing_id=True):
        """Enregistre l'intention de déplacer les emails côté serveur.

        sudo : la file est un objet technique, et l'écriture distante suppose
        le mot de passe IMAP, hors de portée de l'utilisateur.

        immediate=False depuis la passerelle entrante : ouvrir une connexion
        IMAP pendant le traitement d'un email entrant ralentirait la relève et
        la ferait échouer en cascade si le serveur tousse.

        notify_missing_id=False depuis la passerelle entrante : la note dans le
        chatter promet une action de l'utilisateur qui n'a pas eu lieu — pour un
        email qui vient d'arriver, elle serait un faux souvenir. Le journal
        applicatif suffit à qui doit diagnostiquer."""
        Action = self.env['oski.mail.imap.action'].sudo()
        actions = Action.browse()
        for record in self:
            if not (record.email_message_id and record.mailbox_id):
                _logger.info(
                    'Messagerie : geste %s sans identifiant de message, aucune action '
                    'distante créée (fiche %s)', operation, record.id)
                if notify_missing_id:
                    record.message_post(body=_(
                        "Aucun identifiant de message : cet email n'a pas pu être "
                        "déplacé sur le serveur."))
                continue
            actions |= Action.create({
                'mailbox_id': record.mailbox_id.id,
                'inbox_id': record.id,
                'email_message_id': record.email_message_id,
                'operation': operation,
            })
        if actions and immediate:
            actions._run_grouped()
        return actions

    def action_delete_email(self):
        """Supprimer : corbeille côté serveur, fiche archivée côté Odoo.

        La fiche n'est jamais détruite — elle porte la réponse envoyée depuis
        Odoo, qui n'existe nulle part ailleurs."""
        self._oski_imap_dispatch('trash')
        self.write({'active': False})
        return True

    def action_mark_spam(self):
        Blocklist = self.env['oski.mail.blocklist']
        # Ne jamais bloquer une des boîtes du module elle-même : un mauvais
        # clic sur un message auto-envoyé/relayé par une de nos boîtes ne
        # doit pas nous couper de notre propre adresse, sans retour possible
        # pour un simple utilisateur. Le déplacement en indésirable reste
        # effectué, seule la mémorisation est sautée.
        own_addresses = set(filter(None, (
            email_normalize(email)
            for email in self.env['oski.mailbox'].sudo().search([]).mapped('email'))))
        for record in self:
            if record.email_from and email_normalize(record.email_from) not in own_addresses:
                Blocklist._block(record.email_from, origin_inbox=record)
        self._oski_imap_dispatch('junk')
        self.write({'state': 'spam', 'active': False})
        return True

    def action_mark_done(self):
        self.write({'state': 'done'})

    def action_mark_new(self):
        self.write({'state': 'new'})

    def _reply_body(self):
        """Corps initial d'une réponse : signature puis citation de l'original."""
        self.ensure_one()
        Draft = self.env['oski.mail.draft']
        quote = Markup(
            '<blockquote style="border-left:2px solid #ccc;padding-left:12px;color:#666;">'
            '<p>Le %(date)s, %(author)s a écrit :</p>%(body)s</blockquote>'
        ) % {
            'date': format_datetime(self.env, self.date_received),
            'author': self.email_from or '',
            'body': Markup(self.body_html or ''),
        }
        return Markup('<p><br/></p>') + Draft._signature_block(self.mailbox_id) + quote

    def _open_draft(self, draft):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'oski.mail.draft',
            'view_mode': 'form',
            'res_id': draft.id,
            'target': 'current',
        }

    def action_reply(self):
        self.ensure_one()
        if not self.mailbox_id:
            raise UserError(_(
                "Cette fiche n'a plus de boîte associée (supprimée depuis) : "
                "impossible de choisir un expéditeur pour la réponse."))
        subject = self.subject or ''
        if not subject.lower().startswith('re:'):
            subject = 'Re: %s' % subject
        draft = self.env['oski.mail.draft'].create({
            'mailbox_id': self.mailbox_id.id,
            'inbox_id': self.id,
            'email_to': self.email_from,
            'subject': subject,
            'body_html': self._reply_body(),
        })
        return self._open_draft(draft)

    @api.model
    def action_new_message(self):
        mailbox = self.env['oski.mailbox'].search([], limit=1)
        if not mailbox:
            raise UserError(_(
                "Aucune boîte email n'est configurée : impossible de choisir "
                "un expéditeur. Configurez d'abord une boîte."))
        draft = self.env['oski.mail.draft'].create({
            'mailbox_id': mailbox.id,
            'subject': '',
            'email_to': '',
            'body_html': self.env['oski.mail.draft']._signature_block(mailbox),
        })
        return self._open_draft(draft)

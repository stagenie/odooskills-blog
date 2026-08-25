import logging

from odoo import api, fields, models, _
from odoo.tools import email_normalize, formataddr

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
        return super().message_new(msg_dict, custom_values=values)

    def message_update(self, msg_dict, update_vals=None):
        vals = dict(update_vals or {})
        vals['date_received'] = msg_dict.get('date') or fields.Datetime.now()
        if self.state != 'spam':
            # Une relance ranime le fil : on le sort d'archive et on le
            # remet en Nouveau. Un fil marqué indésirable reste indésirable
            # et archivé : c'est tout le sens du marquage, la routing ne
            # doit pas le ramener en tête de boîte.
            vals['state'] = 'new'
            vals['active'] = True
        if not self.email_message_id and msg_dict.get('message_id'):
            vals['email_message_id'] = msg_dict['message_id']
        return super().message_update(msg_dict, update_vals=vals)

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
        for record in self.filtered(lambda r: r.mailbox_id.email):
            result[record.id] = formataddr(
                (record.mailbox_id.name or record.mailbox_id.email,
                 record.mailbox_id.email))
        return result

    @api.depends('imap_action_ids.state')
    def _compute_imap_pending(self):
        for record in self:
            record.imap_pending = any(
                action.state == 'pending' for action in record.imap_action_ids)
            record.imap_failed = any(
                action.state == 'failed' for action in record.imap_action_ids)

    def _oski_imap_dispatch(self, operation, immediate=True):
        """Enregistre l'intention de déplacer les emails côté serveur.

        sudo : la file est un objet technique, et l'écriture distante suppose
        le mot de passe IMAP, hors de portée de l'utilisateur.

        immediate=False depuis la passerelle entrante : ouvrir une connexion
        IMAP pendant le traitement d'un email entrant ralentirait la relève et
        la ferait échouer en cascade si le serveur tousse."""
        Action = self.env['oski.mail.imap.action'].sudo()
        actions = Action.browse()
        for record in self:
            if not (record.email_message_id and record.mailbox_id):
                _logger.info(
                    'Messagerie : geste %s sans identifiant de message, aucune action '
                    'distante créée (fiche %s)', operation, record.id)
                record.message_post(body=_(
                    "Aucun identifiant de message : cet email n'a pas pu être déplacé "
                    "sur le serveur."))
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
        self._oski_imap_dispatch('junk')
        self.write({'state': 'spam', 'active': False})
        return True

    def action_mark_done(self):
        self.write({'state': 'done'})

    def action_mark_new(self):
        self.write({'state': 'new'})

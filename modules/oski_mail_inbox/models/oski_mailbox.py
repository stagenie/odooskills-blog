import imaplib
import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

BACKLOG_BATCH_SIZE = 200
# IMAP exige les abréviations de mois anglaises ; strftime('%b') dépend de la locale.
IMAP_MONTHS = ('Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
               'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec')


class OskiMailbox(models.Model):
    _name = 'oski.mailbox'
    _description = 'Boîte email OdooSkills'
    _order = 'email'

    name = fields.Char(string='Nom', required=True)
    email = fields.Char(string='Adresse email', required=True)
    color = fields.Integer(string='Couleur')
    active = fields.Boolean(default=True)
    imap_host = fields.Char(string='Serveur IMAP')
    imap_port = fields.Integer(string='Port IMAP', default=993)
    imap_ssl = fields.Boolean(string='SSL/TLS', default=True)
    imap_user = fields.Char(string='Utilisateur IMAP')
    imap_password = fields.Char(string='Mot de passe IMAP', groups='base.group_system')
    fetchmail_server_id = fields.Many2one(
        'fetchmail.server', string='Serveur entrant', readonly=True, copy=False)
    backlog_state = fields.Selection([
        ('none', 'Aucun'),
        ('pending', 'En attente'),
        ('running', 'En cours'),
        ('done', 'Terminé'),
    ], string='Import historique', default='none', copy=False)
    backlog_since = fields.Date(
        string='Importer depuis', default=lambda self: fields.Date.to_date('2026-01-01'),
        help="Seuls les emails reçus à partir de cette date sont importés (INBOX uniquement).")
    backlog_last_uid = fields.Integer(string='Dernier UID importé', default=0, copy=False)
    backlog_done_count = fields.Integer(string='Emails importés', default=0, copy=False)

    _email_unique = models.Constraint(
        'UNIQUE (email)', "Une boîte existe déjà avec cette adresse.")

    @api.model_create_multi
    def create(self, vals_list):
        boxes = super().create(vals_list)
        boxes._sync_fetchmail_server()
        return boxes

    def write(self, vals):
        res = super().write(vals)
        if any(f in vals for f in (
                'name', 'email', 'active',
                'imap_host', 'imap_port', 'imap_ssl', 'imap_user', 'imap_password')):
            self._sync_fetchmail_server()
        return res

    def unlink(self):
        servers = self.sudo().fetchmail_server_id
        res = super().unlink()
        servers.unlink()
        return res

    def _sync_fetchmail_server(self):
        """Crée/synchronise le fetchmail.server natif de chaque boîte.

        sudo : fetchmail.server est un objet de configuration réservé à
        base.group_system ; sa gestion est un effet technique du CRUD boîte,
        pas un accès utilisateur à des données métier."""
        model_inbox = self.env['ir.model'].sudo().search(
            [('model', '=', 'oski.mail.inbox')], limit=1)
        for box in self:
            box_sudo = box.sudo()
            if not (box_sudo.imap_host and box_sudo.imap_user and box_sudo.imap_password):
                continue
            server_vals = {
                'name': 'Messagerie — %s' % box_sudo.email,
                'server_type': 'imap',
                'server': box_sudo.imap_host,
                'port': box_sudo.imap_port or 993,
                'is_ssl': box_sudo.imap_ssl,
                'user': box_sudo.imap_user,
                'password': box_sudo.imap_password,
                'object_id': model_inbox.id,
                'active': box_sudo.active,
                'attach': True,
                'original': False,
            }
            if box_sudo.fetchmail_server_id:
                box_sudo.fetchmail_server_id.write(server_vals)
            else:
                server = self.env['fetchmail.server'].sudo().create(server_vals)
                box_sudo.fetchmail_server_id = server

    def action_test_connection(self):
        self.ensure_one()
        if not self.fetchmail_server_id:
            return
        return self.sudo().fetchmail_server_id.button_confirm_login()

    def action_start_backlog(self):
        for box in self:
            box.write({
                'backlog_state': 'pending',
                'backlog_last_uid': 0,
            })

    @api.model
    def _imap_since_criteria(self, since_date):
        return '(SINCE "%02d-%s-%d")' % (
            since_date.day, IMAP_MONTHS[since_date.month - 1], since_date.year)

    def _imap_connect(self):
        self.ensure_one()
        box = self.sudo()
        if not (box.imap_host and box.imap_user and box.imap_password):
            raise UserError(_("Configuration IMAP incomplète pour %s.", box.email))
        klass = imaplib.IMAP4_SSL if box.imap_ssl else imaplib.IMAP4
        connection = klass(box.imap_host, box.imap_port or (993 if box.imap_ssl else 143))
        connection.login(box.imap_user, box.imap_password)
        return connection

    @api.model
    def _cron_process_backlog(self):
        boxes = self.search([('backlog_state', 'in', ('pending', 'running'))])
        for box in boxes:
            try:
                box._process_backlog_batch()
            except Exception:
                _logger.exception(
                    'Messagerie : échec import historique pour %s', box.email)

    def _process_backlog_batch(self):
        """Importe une tranche d'historique depuis INBOX (lecture seule).

        Relançable : la progression est tenue par backlog_last_uid et la
        dédup Message-Id du gateway absorbe tout recouvrement. Commit après
        chaque message (pattern fetchmail natif), désactivable en test via
        le contexte oski_backlog_no_commit."""
        self.ensure_one()
        no_commit = self.env.context.get('oski_backlog_no_commit')
        connection = self._imap_connect()
        try:
            connection.select('INBOX', readonly=True)
            since = self.backlog_since or fields.Date.to_date('2026-01-01')
            status, data = connection.uid('search', None, self._imap_since_criteria(since))
            if status != 'OK':
                raise UserError(_("Recherche IMAP en échec pour %s.", self.email))
            uids = sorted(int(u) for u in (data[0].split() if data and data[0] else []))
            pending = [u for u in uids if u > self.backlog_last_uid][:BACKLOG_BATCH_SIZE]
            if not pending:
                self.write({'backlog_state': 'done'})
                if not no_commit:
                    self.env.cr.commit()
                return
            self.write({'backlog_state': 'running'})
            MailThread = self.env['mail.thread'].with_context(
                default_fetchmail_server_id=self.fetchmail_server_id.id)
            for uid in pending:
                status, msg_data = connection.uid('fetch', str(uid), '(BODY.PEEK[])')
                raw = msg_data[0][1] if status == 'OK' and msg_data and msg_data[0] else None
                if raw:
                    try:
                        MailThread.message_process(
                            'oski.mail.inbox', raw, strip_attachments=False)
                    except Exception:
                        _logger.exception(
                            'Messagerie : message UID %s illisible sur %s, ignoré',
                            uid, self.email)
                self.write({
                    'backlog_last_uid': uid,
                    'backlog_done_count': self.backlog_done_count + 1,
                })
                if not no_commit:
                    self.env.cr.commit()
            if len(pending) < BACKLOG_BATCH_SIZE:
                self.write({'backlog_state': 'done'})
                if not no_commit:
                    self.env.cr.commit()
        finally:
            try:
                connection.logout()
            except Exception:
                pass

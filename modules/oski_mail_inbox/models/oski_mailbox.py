import imaplib
import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

BACKLOG_BATCH_SIZE = 200
# IMAP exige les abréviations de mois anglaises ; strftime('%b') dépend de la locale.
IMAP_MONTHS = ('Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
               'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec')

# Noms de repli, testés par SELECT quand le serveur n'annonce pas SPECIAL-USE.
# ASCII uniquement : un nom accentué serait encodé en IMAP-UTF-7 modifié
# (« Indésirables » -> « Ind&AOk-sirables ») et ne se devine pas. Ces
# serveurs-là annoncent presque toujours SPECIAL-USE.
TRASH_CANDIDATES = ('Trash', 'INBOX.Trash', 'Deleted Items', 'Deleted Messages', 'Corbeille')
JUNK_CANDIDATES = ('Junk', 'INBOX.Junk', 'Junk E-mail', 'Spam', 'INBOX.Spam')
SPECIAL_USE_FLAGS = {'trash': b'\\trash', 'junk': b'\\junk'}
FOLDER_FIELDS = {'trash': 'trash_folder', 'junk': 'junk_folder'}


class OskiMailbox(models.Model):
    _name = 'oski.mailbox'
    _description = 'Boîte email'
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
    trash_folder = fields.Char(
        string='Dossier corbeille',
        help="Laissez vide : le dossier est détecté puis mémorisé automatiquement.")
    junk_folder = fields.Char(
        string='Dossier indésirables',
        help="Laissez vide : le dossier est détecté puis mémorisé automatiquement.")
    fetchmail_server_id = fields.Many2one(
        'fetchmail.server', string='Serveur entrant', readonly=True, copy=False)
    backlog_state = fields.Selection([
        ('none', 'Aucun'),
        ('pending', 'En attente'),
        ('running', 'En cours'),
        ('done', 'Terminé'),
    ], string='Import historique', default='none', copy=False)
    backlog_since = fields.Date(
        string='Importer depuis', default=lambda self: self._default_backlog_since(),
        help="Seuls les emails reçus à partir de cette date sont importés (INBOX uniquement).")
    backlog_last_uid = fields.Integer(string='Dernier UID importé', default=0, copy=False)
    backlog_done_count = fields.Integer(string='Emails importés', default=0, copy=False)

    _email_unique = models.Constraint(
        'UNIQUE (email)', "Une boîte existe déjà avec cette adresse.")

    @api.model
    def _default_backlog_since(self):
        """1ᵉʳ janvier de l'année en cours. Une année en dur vieillit mal
        dans un module distribué."""
        return fields.Date.to_date('%d-01-01' % fields.Date.today().year)

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
    def _imap_quote(self, value):
        """Encadre un nom de dossier ou une valeur de recherche pour IMAP."""
        escaped = (value or '').replace('\\', '\\\\').replace('"', '\\"')
        return '"%s"' % escaped

    @api.model
    def _imap_parse_list_name(self, line):
        """Extrait le nom de dossier d'une ligne de réponse LIST.

        Forme typique : (\\HasNoChildren \\Trash) "." "INBOX.Trash"
        """
        if isinstance(line, tuple):
            line = b' '.join(part for part in line if isinstance(part, bytes))
        text = line.decode('utf-8', 'replace').strip()
        if text.endswith('"'):
            start = text.rfind('"', 0, -1)
            if start != -1:
                return text[start + 1:-1]
        return text.rsplit(' ', 1)[-1].strip('"')

    def _imap_resolve_folder(self, connection, kind):
        """Retourne le nom du dossier distant pour 'trash' ou 'junk'.

        Ordre : valeur saisie, puis attribut SPECIAL-USE annoncé par LIST,
        puis noms courants testés par SELECT. Le résultat est mémorisé pour
        ne pas refaire la découverte à chaque geste."""
        self.ensure_one()
        field = FOLDER_FIELDS[kind]
        if self[field]:
            return self[field]

        flag = SPECIAL_USE_FLAGS[kind]
        status, lines = connection.list()
        if status == 'OK':
            for line in lines or []:
                raw = line if isinstance(line, bytes) else b' '.join(
                    part for part in line if isinstance(part, bytes))
                if flag in raw.lower():
                    name = self._imap_parse_list_name(line)
                    if name:
                        self.sudo().write({field: name})
                        return name

        candidates = TRASH_CANDIDATES if kind == 'trash' else JUNK_CANDIDATES
        for name in candidates:
            status, _data = connection.select(self._imap_quote(name), readonly=True)
            if status == 'OK':
                self.sudo().write({field: name})
                return name

        raise UserError(_(
            "Aucun dossier « %(kind)s » trouvé sur %(email)s. Essayés : %(names)s. "
            "Saisissez le nom exact dans la configuration de la boîte.",
            kind=_('corbeille') if kind == 'trash' else _('indésirables'),
            email=self.email, names=', '.join(candidates)))

    @api.model
    def _imap_capabilities(self, connection):
        raw = getattr(connection, 'capabilities', ()) or ()
        return tuple(
            capability.decode() if isinstance(capability, bytes) else str(capability)
            for capability in raw)

    def _imap_move_message(self, connection, email_message_id, folder):
        """Déplace un message d'INBOX vers `folder`, sans jamais purger le dossier.

        Retourne 'moved', 'absent' (déjà plus là : objectif atteint) ou
        'copied_not_purged' (serveur sans MOVE ni UIDPLUS)."""
        self.ensure_one()
        status, data = connection.uid(
            'SEARCH', None, 'HEADER', 'Message-ID', self._imap_quote(email_message_id))
        if status != 'OK':
            raise UserError(_("Recherche IMAP en échec sur %s.", self.email))
        uids = data[0].split() if data and data[0] else []
        if not uids:
            # Déjà déplacé, ou supprimé depuis le webmail. L'état visé est
            # atteint : c'est un succès, et c'est ce qui rend la file rejouable.
            return 'absent'

        uid = uids[-1]
        capabilities = self._imap_capabilities(connection)
        quoted = self._imap_quote(folder)

        if 'MOVE' in capabilities:
            status, _data = connection.uid('MOVE', uid, quoted)
            if status == 'OK':
                return 'moved'

        status, _data = connection.uid('COPY', uid, quoted)
        if status != 'OK':
            raise UserError(_(
                "Copie vers %(folder)s impossible sur %(email)s.",
                folder=folder, email=self.email))
        connection.uid('STORE', uid, '+FLAGS', '(\\Deleted)')

        if 'UIDPLUS' in capabilities:
            # UID EXPUNGE ne purge QUE l'UID nommé (RFC 4315). Un EXPUNGE nu
            # purgerait tous les messages \Deleted du dossier, y compris ceux
            # marqués par un autre client au même instant.
            status, _data = connection.uid('EXPUNGE', uid)
            if status == 'OK':
                return 'moved'

        return 'copied_not_purged'

    def action_detect_folders(self):
        """Bouton de configuration : détecte et mémorise les deux dossiers."""
        self.ensure_one()
        connection = self._imap_connect()
        try:
            self._imap_resolve_folder(connection, 'trash')
            self._imap_resolve_folder(connection, 'junk')
        finally:
            try:
                connection.logout()
            except Exception:
                pass
        return True

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
            since = self.backlog_since or self._default_backlog_since()
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

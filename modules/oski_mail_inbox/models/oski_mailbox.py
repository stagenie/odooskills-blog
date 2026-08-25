import base64
import imaplib
import logging
import re

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
    def _imap_utf7_encode(self, value):
        """Nom de dossier IMAP en UTF-7 modifié (RFC 3501 §5.1.3).

        L'ASCII imprimable passe tel quel — un `/` de hiérarchie ou un `+`
        doivent rester eux-mêmes. Seul `&` s'échappe, en `&-`. Le reste part
        en base64 UTF-16BE entre `&` et `-`, avec `,` au lieu de `/`."""
        if not value:
            return value
        out = []
        buffer = []

        def flush():
            if buffer:
                raw = ''.join(buffer).encode('utf-16-be')
                encoded = base64.b64encode(raw).decode('ascii').rstrip('=')
                out.append('&%s-' % encoded.replace('/', ','))
                buffer.clear()

        for char in value:
            if char == '&':
                flush()
                out.append('&-')
            elif '\x20' <= char <= '\x7e':
                flush()
                out.append(char)
            else:
                buffer.append(char)
        flush()
        return ''.join(out)

    @api.model
    def _imap_utf7_decode(self, value):
        """Inverse de _imap_utf7_encode. Ne lève jamais : un nom illisible
        est rendu tel quel plutôt que de faire remonter une trace au lieu
        d'un message."""
        if not value:
            return value
        out = []
        index = 0
        while index < len(value):
            char = value[index]
            if char != '&':
                out.append(char)
                index += 1
                continue
            end = value.find('-', index + 1)
            if end == -1:
                out.append(value[index:])
                break
            run = value[index + 1:end]
            if not run:
                out.append('&')
            else:
                padded = run.replace(',', '/')
                padded += '=' * (-len(padded) % 4)
                try:
                    out.append(base64.b64decode(padded).decode('utf-16-be'))
                except Exception:
                    out.append(value[index:end + 1])
            index = end + 1
        return ''.join(out)

    @api.model
    def _imap_quote_folder(self, name):
        """Encode en UTF-7 modifié puis encadre un nom de dossier pour une
        commande IMAP (SELECT/EXAMINE, COPY, MOVE)."""
        return self._imap_quote(self._imap_utf7_encode(name))

    @api.model
    def _imap_flatten_list_line(self, line):
        """Une ligne de réponse LIST peut arriver en tuple (littéral IMAP) ou
        en bytes simple ; on la ramène toujours à des bytes."""
        if isinstance(line, bytes):
            return line
        return b' '.join(part for part in line if isinstance(part, bytes))

    @api.model
    def _imap_parse_list_name(self, line):
        """Extrait, décodé, le nom de dossier d'une ligne de réponse LIST.

        Forme typique : (\\HasNoChildren \\Trash) "." "INBOX.Trash"
        """
        raw = self._imap_flatten_list_line(line)
        text = raw.decode('utf-8', 'replace').strip()
        if text.endswith('"'):
            start = text.rfind('"', 0, -1)
            if start != -1:
                return self._imap_utf7_decode(text[start + 1:-1])
        return self._imap_utf7_decode(text.rsplit(' ', 1)[-1].strip('"'))

    def _imap_resolve_folder(self, connection, kind, force=False):
        """Retourne le nom (décodé) du dossier distant pour 'trash' ou 'junk'.

        Ordre : valeur saisie (sauf force=True), puis attribut SPECIAL-USE
        annoncé par LIST, puis noms courants testés par SELECT. Le résultat
        est mémorisé pour ne pas refaire la découverte à chaque geste.
        force=True (bouton de configuration) ignore la valeur mémorisée, pour
        pouvoir corriger une détection erronée ou un dossier renommé côté
        serveur ; en cas d'échec, la valeur mémorisée n'est pas effacée."""
        self.ensure_one()
        field = FOLDER_FIELDS[kind]
        if self[field] and not force:
            return self[field]

        flag = SPECIAL_USE_FLAGS[kind]
        status, lines = connection.list()
        if status == 'OK':
            for line in lines or []:
                raw = self._imap_flatten_list_line(line)
                if flag in raw.lower():
                    name = self._imap_parse_list_name(line)
                    if name:
                        self.sudo().write({field: name})
                        return name

        candidates = TRASH_CANDIDATES if kind == 'trash' else JUNK_CANDIDATES
        for name in candidates:
            status, _data = connection.select(self._imap_quote_folder(name), readonly=True)
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

    @api.model
    def _imap_header_message_id(self, data):
        """Extrait la valeur de l'en-tête Message-ID d'une réponse FETCH
        BODY[HEADER.FIELDS (MESSAGE-ID)] : data[0] est un tuple
        (descripteur, contenu littéral)."""
        if not data or not data[0] or not isinstance(data[0], tuple):
            return None
        header_bytes = data[0][1] or b''
        text = header_bytes.decode('utf-8', 'replace')
        match = re.search(r'(?im)^Message-ID:\s*(.+?)\s*$', text)
        return match.group(1).strip() if match else None

    def _imap_exact_message_id_matches(self, connection, uids, email_message_id):
        """`SEARCH HEADER` est un filtre par sous-chaîne (RFC 3501) : il peut
        retourner un message dont le Message-ID CONTIENT celui demandé sans
        lui être égal (`<abc@x>` matche aussi `<sub-abc@x>`). On revérifie
        chaque candidat par un FETCH d'en-tête et on ne garde que l'égalité
        exacte, pour ne jamais déplacer le mauvais message.

        Si un FETCH échoue et qu'aucun autre candidat ne confirme un match
        exact, on ne peut pas distinguer « vérifié absent » de « pas pu
        vérifier » : mieux vaut lever que rendre 'absent', qui est un
        succès contractuel et arrêterait la file à tort."""
        exact = []
        verification_failed = False
        for uid in uids:
            status, data = connection.uid(
                'FETCH', uid, '(BODY.PEEK[HEADER.FIELDS (MESSAGE-ID)])')
            if status != 'OK':
                verification_failed = True
                continue
            if self._imap_header_message_id(data) == email_message_id:
                exact.append(uid)
        if not exact and verification_failed:
            raise UserError(_(
                "Vérification IMAP en échec sur %s : impossible de confirmer "
                "si le message est toujours présent.", self.email))
        return exact

    def _imap_move_message(self, connection, email_message_id, folder):
        """Déplace vers `folder` tous les messages d'INBOX dont le
        Message-ID est exactement `email_message_id`, sans jamais purger le
        dossier au-delà des UID déplacés.

        Retourne 'moved' (tous déplacés), 'absent' (aucun match exact :
        déjà déplacé, supprimé depuis le webmail, ou faux positif de
        sous-chaîne — l'état visé est atteint, c'est un succès) ou
        'copied_not_purged' (au moins un message copié sans être purgé)."""
        self.ensure_one()
        status, _data = connection.select('INBOX')
        if status != 'OK':
            raise UserError(_("Impossible de sélectionner INBOX sur %s.", self.email))

        status, data = connection.uid(
            'SEARCH', None, 'HEADER', 'Message-ID', self._imap_quote(email_message_id))
        if status != 'OK':
            raise UserError(_("Recherche IMAP en échec sur %s.", self.email))
        candidates = data[0].split() if data and data[0] else []
        uids = self._imap_exact_message_id_matches(connection, candidates, email_message_id)
        if not uids:
            return 'absent'

        capabilities = self._imap_capabilities(connection)
        results = [
            self._imap_move_one_uid(connection, uid, folder, capabilities)
            for uid in uids]
        return 'moved' if all(result == 'moved' for result in results) else 'copied_not_purged'

    def _imap_move_one_uid(self, connection, uid, folder, capabilities):
        """Déplace un seul UID déjà confirmé (Message-ID exact), en
        cascade : UID MOVE, puis COPY + UID EXPUNGE, puis simple marquage
        \\Deleted sans purge."""
        quoted = self._imap_quote_folder(folder)

        if 'MOVE' in capabilities:
            status, _data = connection.uid('MOVE', uid, quoted)
            if status == 'OK':
                return 'moved'

        status, _data = connection.uid('COPY', uid, quoted)
        if status != 'OK':
            raise UserError(_(
                "Copie vers %(folder)s impossible sur %(email)s.",
                folder=folder, email=self.email))

        status, _data = connection.uid('STORE', uid, '+FLAGS', '(\\Deleted)')
        if status != 'OK':
            # Le message n'est pas marqué \Deleted : un EXPUNGE, même ciblé
            # par UID, ne purgerait rien pour lui et ne prouverait rien.
            return 'copied_not_purged'

        if 'UIDPLUS' in capabilities:
            # UID EXPUNGE ne purge QUE l'UID nommé (RFC 4315). Un EXPUNGE nu
            # purgerait tous les messages \Deleted du dossier, y compris ceux
            # marqués par un autre client au même instant.
            status, _data = connection.uid('EXPUNGE', uid)
            if status == 'OK':
                return 'moved'

        return 'copied_not_purged'

    def action_detect_folders(self):
        """Bouton de configuration : redétecte et mémorise les deux
        dossiers, même si un nom (possiblement erroné) est déjà
        enregistré."""
        self.ensure_one()
        connection = self._imap_connect()
        try:
            self._imap_resolve_folder(connection, 'trash', force=True)
            self._imap_resolve_folder(connection, 'junk', force=True)
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

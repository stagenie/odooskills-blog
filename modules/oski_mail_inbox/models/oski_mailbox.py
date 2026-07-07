import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


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

import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 5


class OskiMailImapAction(models.Model):
    _name = 'oski.mail.imap.action'
    _description = 'Action IMAP en attente'
    _order = 'create_date desc, id desc'
    _rec_name = 'email_message_id'

    mailbox_id = fields.Many2one(
        'oski.mailbox', string='Boîte', required=True, ondelete='cascade', index=True)
    inbox_id = fields.Many2one(
        'oski.mail.inbox', string='Email', ondelete='set null', index=True)
    email_message_id = fields.Char(string='Identifiant du message', required=True)
    operation = fields.Selection([
        ('trash', 'Corbeille'),
        ('junk', 'Indésirables'),
    ], string='Opération', required=True)
    state = fields.Selection([
        ('pending', 'En attente'),
        ('done', 'Fait'),
        ('failed', 'Échec'),
    ], string='État', default='pending', index=True)
    result = fields.Selection([
        ('moved', 'Déplacé'),
        ('absent', 'Déjà absent'),
        ('copied_not_purged', 'Copié, purge non supportée'),
    ], string='Résultat', readonly=True)
    attempts = fields.Integer(string='Tentatives', default=0)
    last_error = fields.Text(string='Dernière erreur', readonly=True)

    def _register_failure(self, message):
        """Consigne un échec et retire de la file au-delà du plafond."""
        for action in self:
            attempts = action.attempts + 1
            action.write({
                'attempts': attempts,
                'last_error': message,
                'state': 'failed' if attempts >= MAX_ATTEMPTS else 'pending',
            })

    def _run_on(self, connection):
        """Exécute une action sur une connexion déjà ouverte et sélectionnée.

        Le corps est protégé par un savepoint : `_imap_resolve_folder` écrit en
        base (il mémorise le dossier résolu), et une erreur serveur survenant
        après cette écriture avorterait le curseur — le `write` de
        `_register_failure` lèverait alors à son tour, et l'exception
        s'échapperait de `_run_grouped` malgré sa promesse de ne jamais lever."""
        self.ensure_one()
        try:
            with self.env.cr.savepoint():
                folder = self.mailbox_id._imap_resolve_folder(connection, self.operation)
                result = self.mailbox_id._imap_move_message(
                    connection, self.email_message_id, folder)
        except Exception as error:  # noqa: BLE001 - toute panne serveur reste en file
            _logger.warning('Messagerie : action IMAP %s en échec (%s)', self.id, error)
            self._register_failure(str(error))
            return False
        self.write({'state': 'done', 'result': result, 'last_error': False})
        return True

    def _run_grouped(self):
        """Exécute les actions, une seule connexion par boîte.

        Ne lève jamais : un geste utilisateur ne doit pas échouer parce que le
        serveur distant est indisponible. L'échec reste en file.

        Ne retraite que ce qui est encore 'pending' : un appelant (le bouton
        Rejouer notamment) peut transmettre un lot mêlant des actions déjà
        closes, qui ne doivent pas être rejouées une seconde fois."""
        actions = self.filtered(lambda action: action.state == 'pending')
        for mailbox, group in actions.grouped('mailbox_id').items():
            try:
                connection = mailbox._imap_connect()
            except Exception as error:  # noqa: BLE001
                _logger.warning(
                    'Messagerie : connexion IMAP impossible pour %s (%s)',
                    mailbox.email, error)
                group._register_failure(str(error))
                continue
            try:
                for action in group:
                    action._run_on(connection)
            finally:
                try:
                    connection.logout()
                except Exception:  # noqa: BLE001
                    pass

    @api.model
    def _cron_process_imap_actions(self):
        self.search([('state', '=', 'pending')], order='id asc')._run_grouped()

    def action_retry(self):
        """Bouton Manager : remet une action en échec dans la file.

        Ne réinitialise pas `attempts` — une action déjà tombée au plafond ne
        doit pas repartir avec un budget de tentatives neuf, seulement avec
        une occasion de plus avant de retomber en échec."""
        actions = self.filtered(lambda action: action.state != 'done')
        actions.write({'state': 'pending', 'last_error': False})
        actions._run_grouped()
        return True

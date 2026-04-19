from odoo import api, models, fields
from odoo.exceptions import ValidationError


class HelpdeskTicket(models.Model):
    """Ticket de support — modèle persistant.

    Hérite de models.Model : données stockées en base PostgreSQL,
    durée de vie illimitée, visible dans les vues backend.
    """
    _name = 'helpdesk.ticket'
    _description = 'Ticket Helpdesk'
    _inherit = [
        'mail.thread',
        'mail.activity.mixin',
        'odooskills.helpdesk.mixin',
        'odooskills.sla.mixin',
    ]
    _order = 'priority desc, create_date desc'
    _rec_name = 'name'

    # Contrainte d'unicité en Odoo 19 — remplace _sql_constraints
    _unique_reference = models.Constraint(
        'UNIQUE (reference)',
        "La référence du ticket doit être unique.",
    )

    # ── Champs de base (T08/T09) ──────────────────────────────────────────────
    name = fields.Char(string='Sujet', required=True, tracking=True)
    reference = fields.Char(string='Référence', copy=False, index=True)
    description = fields.Text(string='Description')
    category_id = fields.Many2one(
        comodel_name='helpdesk.ticket.category',
        string='Catégorie',
        ondelete='restrict',
    )
    partner_id = fields.Many2one('res.partner', string='Client')
    state = fields.Selection(
        selection=[
            ('new', 'Nouveau'),
            ('in_progress', 'En cours'),
            ('done', 'Résolu'),
        ],
        default='new',
        required=True,
        tracking=True,
    )

    # ── Champs relationnels ajoutés (T11) ────────────────────────────────────

    # Many2one : FK vers res.users — un ticket est assigné à un seul agent
    user_id = fields.Many2one(
        comodel_name='res.users',
        string='Assigné à',
        tracking=True,
        ondelete='set null',   # si l'utilisateur est supprimé, le champ passe à False
        index=True,
    )

    # Many2many : un ticket peut avoir plusieurs tags ; un tag peut être sur plusieurs tickets
    # Odoo crée automatiquement la table de liaison helpdesk_ticket_tag_rel
    tag_ids = fields.Many2many(
        comodel_name='helpdesk.ticket.tag',
        string='Tags',
    )

    # One2many : inverse de helpdesk.ticket.comment.ticket_id
    # Pas de colonne PG ici — c'est une vue sur la FK du modèle enfant
    comment_ids = fields.One2many(
        comodel_name='helpdesk.ticket.comment',
        inverse_name='ticket_id',  # nom de l'attribut Many2one dans le modèle enfant
        string='Commentaires',
    )

    # ── Champs non-relationnels (T10) ─────────────────────────────────────────

    # Date : stocke uniquement la date (YYYY-MM-DD), pas l'heure
    deadline = fields.Date(string='Échéance', tracking=True)

    # Datetime : date + heure UTC en base, converti TZ utilisateur à l'affichage
    resolved_at = fields.Datetime(string='Résolu le', readonly=True)

    # Float : nombre décimal ; digits=(6,2) → 6 chiffres au total, 2 après la virgule
    hours_spent = fields.Float(string='Heures passées', digits=(6, 2))

    # Integer : entier signé 32 bits
    incident_count = fields.Integer(string='Nb incidents liés', default=0)

    # Boolean : True/False, stocké BOOLEAN en PG, jamais NULL (False si non renseigné)
    is_urgent = fields.Boolean(string='Urgent', default=False, tracking=True)

    # Priority : Selection pour le widget étoiles (T17)
    # selection_add : étend la selection héritée de mail.thread pour éviter le
    # warning "overrides existing selection"
    priority = fields.Selection(
        selection_add=[
            ('0', 'Normale'),
            ('1', 'Importante'),
            ('2', 'Haute'),
            ('3', 'Urgente'),
        ],
        ondelete={'1': 'set default', '2': 'set default', '3': 'set default'},
        string='Priorité',
        default='0',
        tracking=True,
    )

    # Kanban state : indicateur visuel sur la carte kanban (T17)
    kanban_state = fields.Selection(
        selection=[
            ('normal', 'En cours'),
            ('done', 'Prêt'),
            ('blocked', 'Bloqué'),
        ],
        string='État kanban',
        default='normal',
        tracking=True,
    )

    # Selection : liste fermée de valeurs ; tracking=True trace chaque changement
    channel = fields.Selection(
        selection=[
            ('email', 'Email'),
            ('phone', 'Téléphone'),
            ('portal', 'Portail'),
            ('chat', 'Chat'),
        ],
        string='Canal',
        tracking=True,
    )

    # Text : texte long multi-lignes (textarea), pas de formatage HTML
    resolution_note = fields.Text(string='Note de résolution')

    # Html : texte riche avec éditeur WYSIWYG intégré Odoo
    body_html = fields.Html(string='Corps HTML', sanitize=True)

    # Binary : fichier binaire brut ; attachment=True → stocké dans ir.attachment
    screenshot = fields.Binary(string='Capture d\'écran', attachment=True)

    # Image : spécialisation de Binary avec redimensionnement automatique
    # max_width/max_height : Odoo redimensionne au save si dépassement
    avatar = fields.Image(
        string='Avatar',
        max_width=256,
        max_height=256,
    )

    # Monetary : montant décimal lié à une devise — TOUJOURS associer currency_field
    estimated_cost = fields.Monetary(
        string='Coût estimé',
        currency_field='currency_id',
    )

    # Many2one requis par Monetary — res.currency est le modèle natif Odoo des devises
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Devise',
        default=lambda self: self.env.company.currency_id,
    )

    # ── Champs calculés & contraintes (T12) ───────────────────────────────────

    # Computed Float : nombre de jours entre création et échéance
    # store=False (défaut) → calculé à la volée, pas stocké en base
    duration = fields.Float(
        string='Durée (jours)',
        compute='_compute_duration',
        help="Nombre de jours entre la date de création et l'échéance.",
    )

    # Computed Boolean stocké : recalculé et persisté en base
    # store=True → cherchable, filtrable, visible dans les listes
    is_overdue = fields.Boolean(
        string='En retard',
        compute='_compute_is_overdue',
        store=True,
    )

    @api.depends('deadline', 'create_date')
    def _compute_duration(self):
        """Calcule le nombre de jours entre création et échéance."""
        for ticket in self:
            if ticket.deadline and ticket.create_date:
                delta = ticket.deadline - ticket.create_date.date()
                ticket.duration = delta.days
            else:
                ticket.duration = 0.0

    @api.depends('deadline', 'state')
    def _compute_is_overdue(self):
        """True si l'échéance est dépassée et le ticket n'est pas résolu."""
        today = fields.Date.today()
        for ticket in self:
            ticket.is_overdue = (
                bool(ticket.deadline)
                and ticket.deadline < today
                and ticket.state != 'done'
            )

    @api.constrains('deadline', 'resolved_at')
    def _check_dates(self):
        """Contrainte Python : la résolution ne peut pas précéder l'échéance."""
        for ticket in self:
            if ticket.deadline and ticket.resolved_at:
                if ticket.resolved_at.date() < ticket.deadline:
                    raise ValidationError(
                        "La date de résolution ne peut pas être antérieure à l'échéance."
                    )

    # ── Surcharges CRUD (T15) ─────────────────────────────────────────────────
    # Champs que l'on autorise à modifier même quand le ticket est résolu
    _EDITABLE_WHEN_DONE = {'resolution_note', 'tag_ids', 'message_follower_ids'}

    @api.model_create_multi
    def create(self, vals_list):
        """Surcharge create : génère une référence via ir.sequence si absente.

        @api.model_create_multi : appelé une seule fois avec la liste complète de
        valeurs — compatible batch. C'est l'unique forme acceptée en v19.
        """
        for vals in vals_list:
            if not vals.get('reference'):
                vals['reference'] = self.env['ir.sequence'].sudo().next_by_code(
                    'helpdesk.ticket'
                ) or '/'
        tickets = super().create(vals_list)
        for ticket in tickets:
            ticket.message_post(body=f"Ticket créé — {ticket.reference}")
            # T21 : envoi email d'accusé de réception au client
            if ticket.partner_id.email and not self.env.context.get('skip_mail'):
                template = self.env.ref(
                    'odooskills_helpdesk.mail_template_ticket_opened',
                    raise_if_not_found=False,
                )
                if template:
                    template.send_mail(ticket.id, force_send=False)
        return tickets

    def write(self, vals):
        """Surcharge write : fige les tickets résolus sauf champs whitelistés.

        Démontre le pattern "protection d'état" — très fréquent dans les modules
        métier (factures validées, commandes confirmées, etc.).
        """
        protected = set(vals) - self._EDITABLE_WHEN_DONE
        if protected:
            for ticket in self:
                if ticket.state == 'done':
                    raise ValidationError(
                        f"Ticket {ticket.reference} résolu : seuls "
                        f"{', '.join(sorted(self._EDITABLE_WHEN_DONE))} "
                        "restent modifiables."
                    )
        # Horodatage automatique lors du passage à 'done'
        newly_resolved = self.env['helpdesk.ticket']
        if vals.get('state') == 'done':
            vals.setdefault('resolved_at', fields.Datetime.now())
            newly_resolved = self.filtered(lambda t: t.state != 'done')
        result = super().write(vals)

        # T21 : email de résolution aux tickets qui viennent de passer à 'done'
        if newly_resolved and not self.env.context.get('skip_mail'):
            template = self.env.ref(
                'odooskills_helpdesk.mail_template_ticket_resolved',
                raise_if_not_found=False,
            )
            if template:
                for ticket in newly_resolved:
                    if ticket.partner_id.email:
                        template.send_mail(ticket.id, force_send=False)
        return result

    def unlink(self):
        """Surcharge unlink : interdit la suppression d'un ticket en cours ou résolu."""
        for ticket in self:
            if ticket.state != 'new':
                raise ValidationError(
                    f"Ticket {ticket.reference} ({ticket.state}) : "
                    "seuls les tickets 'Nouveau' peuvent être supprimés."
                )
        return super().unlink()

    # ── Méthodes métier (actions) ─────────────────────────────────────────────

    def action_start(self):
        """Méthode métier : bascule le ticket en 'En cours'.

        Convention Odoo : préfixe action_* pour les méthodes appelables depuis
        les boutons XML. Retourne True/False ou une action client.
        """
        self.ensure_one()
        if self.state != 'new':
            raise ValidationError("Seul un ticket 'Nouveau' peut être démarré.")
        self.write({'state': 'in_progress'})
        return True

    def action_resolve(self):
        """Méthode métier : clôture le ticket."""
        self.ensure_one()
        if self.state == 'done':
            return True
        self.write({'state': 'done'})
        return True

    def action_escalate_sla(self):
        """Escalade : bascule le ticket en priorité 'Urgente' et poste un message.

        Appelable depuis une `ir.actions.server` (manuel) ou un `ir.cron`
        (batch automatique). Idempotent : n'escalade pas un ticket déjà urgent.
        """
        escalated = self.filtered(lambda t: t.state != 'done' and t.priority != '3')
        if not escalated:
            return False
        escalated.write({'priority': '3'})
        for ticket in escalated:
            ticket.message_post(
                body="<p>⚠️ <strong>Escalade SLA automatique</strong> — priorité passée à "
                     "<em>Urgente</em> (échéance imminente).</p>",
            )
        return True

    @api.model
    def _cron_escalate_sla(self):
        """Cron : escalade les tickets dont l'échéance est dans les 24h.

        Tourne toutes les 30 min. Trois critères :
         - state != 'done' (pas les résolus)
         - priority != '3' (pas déjà urgent — idempotence)
         - deadline <= today + 1 jour
        """
        from datetime import timedelta
        threshold = fields.Date.today() + timedelta(days=1)
        tickets = self.search([
            ('state', '!=', 'done'),
            ('priority', '!=', '3'),
            ('deadline', '!=', False),
            ('deadline', '<=', threshold),
        ])
        if tickets:
            tickets.action_escalate_sla()
        return len(tickets)

    def action_open_close_wizard(self):
        """Retourne une action serveur qui ouvre le wizard de clôture.

        Pattern : une méthode qui renvoie un dict `ir.actions.act_window`
        provoque l'ouverture d'une fenêtre côté client. `target='new'`
        ouvre en modal dialog ; le wizard récupère `active_id` via contexte.
        """
        self.ensure_one()
        return {
            'name': 'Clôturer le ticket',
            'type': 'ir.actions.act_window',
            'res_model': 'helpdesk.ticket.close.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_ticket_id': self.id,
                'default_hours_spent': self.hours_spent,
            },
        }

    @api.model
    def count_open_tickets(self):
        """Méthode de classe (@api.model) : ne dépend pas d'un record précis.

        Utilisée par les rapports / dashboards — appelée sur le modèle, pas
        sur un recordset.
        """
        return self.search_count([('state', '!=', 'done')])

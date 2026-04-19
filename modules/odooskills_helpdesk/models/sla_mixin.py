from odoo import api, models, fields


class OdooskillsSlaMixin(models.AbstractModel):
    """Mixin SLA réutilisable — aucune table en base.

    Ajoute trois champs et une méthode de calcul de statut SLA
    à tout modèle qui l'hérite via `_inherit = 'odooskills.sla.mixin'`.

    Exemple d'usage (voir helpdesk.ticket) :
        _inherit = ['mail.thread', 'odooskills.sla.mixin']
    """
    _name = 'odooskills.sla.mixin'
    _description = 'Mixin SLA — délai d\'intervention'

    sla_hours = fields.Integer(
        string='SLA (heures)',
        default=48,
        help="Délai contractuel de traitement en heures.",
    )
    sla_deadline = fields.Datetime(
        string='Échéance SLA',
        compute='_compute_sla_deadline',
        store=True,
    )
    sla_status = fields.Selection(
        selection=[
            ('ok', 'Dans les temps'),
            ('warning', 'Proche de l\'échéance'),
            ('breach', 'SLA dépassé'),
        ],
        string='Statut SLA',
        compute='_compute_sla_status',
        store=True,
    )

    @api.depends('sla_hours', 'create_date')
    def _compute_sla_deadline(self):
        for rec in self:
            if rec.create_date and rec.sla_hours:
                rec.sla_deadline = fields.Datetime.add(
                    rec.create_date, hours=rec.sla_hours,
                )
            else:
                rec.sla_deadline = False

    @api.depends('sla_deadline')
    def _compute_sla_status(self):
        now = fields.Datetime.now()
        for rec in self:
            if not rec.sla_deadline:
                rec.sla_status = 'ok'
                continue
            remaining = (rec.sla_deadline - now).total_seconds() / 3600.0
            if remaining < 0:
                rec.sla_status = 'breach'
            elif remaining < 4:
                rec.sla_status = 'warning'
            else:
                rec.sla_status = 'ok'

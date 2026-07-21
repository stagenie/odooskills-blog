from odoo import fields, models


class MailingContact(models.Model):
    _inherit = 'mailing.contact'

    # Empêche tout doublon d'adresse (insensible à la casse) quelle que soit
    # la voie d'entrée : popup lead-magnet, widget newsletter natif, import,
    # API. Filet dur au niveau base — complète les advisory locks applicatifs
    # qui, eux, évitent l'IntegrityError sur les POST concurrents du même email.
    _email_unique_ci = models.UniqueIndex(
        "(lower(email)) WHERE email IS NOT NULL AND email <> ''"
    )

    email_status = fields.Selection(
        [
            ('valid', 'Valid'),
            ('syntax_ko', 'Syntax KO'),
            ('mx_ko', 'MX KO'),
            ('disposable', 'Disposable domain'),
            ('role_based', 'Role-based'),
            ('dns_timeout', 'DNS timeout'),
        ],
        default='valid',
        readonly=True,
        copy=False,
        help="Result of automated email validation at signup time. "
             "Only 'valid' contacts are persisted at signup; other values "
             "appear only after a posteriori re-validation (sub-project B).",
    )

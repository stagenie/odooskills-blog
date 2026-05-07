from odoo import fields, models


class MailingContact(models.Model):
    _inherit = 'mailing.contact'

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

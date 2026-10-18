import logging

from dateutil.relativedelta import relativedelta
from markupsafe import Markup

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.fields import Domain
from odoo.http.dispatcher import conceal_debug_traceback

_logger = logging.getLogger(__name__)


class LibraryLoan(models.Model):
    _name = 'library.loan'
    _description = "Emprunt"
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _mail_post_access = 'read'
    _order = 'date_out desc, id desc'

    reference = fields.Char(
        string="Référence",
        required=True,
        copy=False,
        readonly=True,
        default="Nouveau",
    )
    member_id = fields.Many2one(
        'library.member',
        string="Adhérent",
        required=True,
        ondelete='cascade',
        tracking=True,
    )
    partner_id = fields.Many2one(
        related='member_id.partner_id',
        string="Contact",
        store=True,
        index=True,
    )
    copy_id = fields.Many2one(
        'library.copy',
        string="Exemplaire",
        required=True,
        ondelete='restrict',
        tracking=True,
    )
    book_id = fields.Many2one(
        related='copy_id.book_id',
        string="Livre",
        store=True,
    )
    genre_ids = fields.Many2many(
        'library.genre',
        'library_loan_genre_rel',
        'loan_id',
        'genre_id',
        related='book_id.genre_ids',
        string="Genres",
        store=True,
    )
    date_out = fields.Date(
        string="Emprunté le",
        required=True,
        default=fields.Date.context_today,
    )
    duration = fields.Integer(string="Durée (jours)", default=14, required=True, tracking=True)
    date_due = fields.Date(
        string="À rendre le",
        compute='_compute_date_due',
        store=True,
        tracking=True,
    )
    date_return = fields.Date(string="Rendu le", readonly=True, copy=False)
    state = fields.Selection(
        [
            ('ongoing', "En cours"),
            ('returned', "Rendu"),
        ],
        string="État",
        default='ongoing',
        required=True,
        tracking=True,
    )
    is_late = fields.Boolean(
        string="En retard",
        compute='_compute_is_late',
        search='_search_is_late',
    )
    days_late = fields.Integer(string="Jours de retard", compute='_compute_is_late')
    reminder_count = fields.Integer(string="Relances", default=0, readonly=True, copy=False)
    reminder_date = fields.Date(string="Dernière relance", readonly=True, copy=False)

    @api.depends('date_out', 'duration')
    def _compute_date_due(self):
        for loan in self:
            if loan.date_out:
                loan.date_due = loan.date_out + relativedelta(days=loan.duration)
            else:
                loan.date_due = False

    @api.depends('date_due', 'date_return', 'state')
    def _compute_is_late(self):
        today = fields.Date.context_today(self)
        for loan in self:
            fin = loan.date_return or today
            loan.is_late = bool(loan.date_due) and loan.state == 'ongoing' and fin > loan.date_due
            loan.days_late = (fin - loan.date_due).days if loan.is_late else 0

    def _search_is_late(self, operator, value):
        if operator != 'in':
            return NotImplemented
        en_retard = Domain('state', '=', 'ongoing') & Domain(
            'date_due', '<', fields.Date.context_today(self)
        )
        return en_retard if True in value else ~en_retard

    @api.constrains('copy_id', 'state')
    def _check_copy_available(self):
        for loan in self:
            if loan.state != 'ongoing':
                continue
            autres = self.search_count([
                ('copy_id', '=', loan.copy_id.id),
                ('state', '=', 'ongoing'),
                ('id', '!=', loan.id),
            ])
            if autres:
                raise ValidationError(self.env._(
                    "L'exemplaire %(exemplaire)s est déjà emprunté.",
                    exemplaire=loan.copy_id.name,
                ))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('reference', "Nouveau") == "Nouveau":
                vals['reference'] = self.env['ir.sequence'].next_by_code(
                    'library.loan', sequence_date=vals.get('date_out'),
                ) or "Nouveau"
        emprunts = super().create(vals_list)
        emprunts.filtered(lambda e: e.state == 'ongoing').copy_id.state = 'borrowed'
        return emprunts

    def action_return(self):
        for loan in self:
            if loan.state == 'returned':
                raise ValidationError(self.env._("Cet emprunt est déjà clos."))
            loan.write({
                'state': 'returned',
                'date_return': fields.Date.context_today(loan),
            })
            loan.copy_id.state = 'available'
            loan.message_post(
                body=Markup("Exemplaire <b>%s</b> rendu et remis en rayon.") % loan.copy_id.name,
                message_type='comment',
                subtype_xmlid='mail.mt_note',
            )

    def action_send_reminder(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': "Relancer l'adhérent",
            'res_model': 'mail.compose.message',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_model': 'library.loan',
                'default_res_ids': self.ids,
                'default_composition_mode': 'comment',
                'default_template_id': self.env.ref('biblio.mail_template_loan_reminder').id,
            },
        }

    def action_print_loan(self):
        return self.env.ref('biblio.action_report_library_loan').report_action(self)

    @api.model
    def _cron_relancer_retards(self):
        aujourdhui = fields.Date.context_today(self)
        a_relancer = self.search(
            Domain('is_late', '=', True)
            & (Domain('reminder_date', '=', False) | Domain('reminder_date', '<', aujourdhui))
        )
        for emprunt in a_relancer:
            emprunt.reminder_count += 1
            emprunt.reminder_date = aujourdhui
            emprunt.message_post_with_source(
                'biblio.mail_template_loan_reminder',
                message_type='comment',
                subtype_xmlid='mail.mt_comment',
            )
        _logger.info("Bibliothèque : %s emprunt(s) en retard relancé(s).", len(a_relancer))
        return len(a_relancer)

    # API JSON-2 : chaque méthode publique est appelable par /json/2/library.loan/<méthode>
    @api.model
    @api.readonly
    @conceal_debug_traceback(UserError)
    def api_loans(self, state='ongoing', late=None, limit=80):
        """Emprunts au format de l'API : une liste de dictionnaires plats."""
        if state not in ('ongoing', 'returned'):
            raise UserError(self.env._("État inconnu : %(state)s.", state=state))
        domain = Domain('state', '=', state)
        if late is not None:
            domain &= Domain('is_late', '=', bool(late))
        return self.search(domain, limit=limit)._api_values()

    @api.model
    @conceal_debug_traceback(UserError)
    def api_return_copy(self, copy):
        """Retour d'un exemplaire par son code d'inventaire (borne de retour)."""
        loan = self.search([('copy_id.name', '=', copy), ('state', '=', 'ongoing')], limit=1)
        if not loan:
            raise UserError(self.env._("Aucun emprunt en cours pour l'exemplaire %(copy)s.", copy=copy))
        loan.action_return()
        return loan._api_values()[0]

    def _api_values(self):
        return [{
            'id': loan.id,
            'reference': loan.reference,
            'member': loan.member_id.card_number,
            'copy': loan.copy_id.name,
            'book': loan.book_id.title,
            'date_out': loan.date_out,
            'date_due': loan.date_due,
            'date_return': loan.date_return or None,
            'days_late': loan.days_late,
        } for loan in self]

    def _compute_access_url(self):
        super()._compute_access_url()
        for loan in self:
            loan.access_url = f'/my/loans/{loan.id}'

    @api.depends('reference', 'copy_id.name')
    def _compute_display_name(self):
        for loan in self:
            loan.display_name = f"{loan.reference} ({loan.copy_id.name})"

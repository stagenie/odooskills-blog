import logging

from odoo import _, api, models, tools

_logger = logging.getLogger(__name__)


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    @api.model_create_multi
    def create(self, vals_list):
        Blacklist = self.env['mail.blacklist'].sudo()
        normalized_to_check = set()
        for vals in vals_list:
            email = vals.get('email_from')
            if not email:
                continue
            email_norm = tools.email_normalize(email)
            if email_norm:
                normalized_to_check.add(email_norm)
        blacklisted = set()
        if normalized_to_check:
            blacklisted = set(Blacklist.search([
                ('email', 'in', list(normalized_to_check)),
                ('active', '=', True),
            ]).mapped('email'))
        for vals in vals_list:
            email = vals.get('email_from')
            if not email:
                continue
            email_norm = tools.email_normalize(email)
            if email_norm and email_norm in blacklisted:
                vals['active'] = False
                _logger.info(
                    "adi_odooskills_crm_antispam: lead from blacklisted email %s "
                    "auto-archived on create", email_norm,
                )
        return super().create(vals_list)

    def action_mark_as_spam(self):
        """ Blacklist email_from + archive self AND all sibling leads sharing
            the same normalized email. Returns a notification action.
        """
        Blacklist = self.env['mail.blacklist'].sudo()
        emails_to_block = set()
        for lead in self:
            if not lead.email_from:
                continue
            email_norm = tools.email_normalize(lead.email_from)
            if email_norm:
                emails_to_block.add(email_norm)

        for email_norm in emails_to_block:
            Blacklist._add(
                email_norm,
                message=_("Blacklisted via SPAM action on CRM lead"),
            )
            _logger.info(
                "adi_odooskills_crm_antispam: email %s blacklisted via SPAM action",
                email_norm,
            )

        siblings = self.env['crm.lead']
        if emails_to_block:
            siblings = self.search([
                ('email_normalized', 'in', list(emails_to_block)),
                ('active', '=', True),
                ('id', 'not in', self.ids),
            ])
        all_leads = self | siblings
        active_leads = all_leads.filtered('active')
        if active_leads:
            active_leads.action_archive()

        msg = _(
            "%(leads)s lead(s) archivé(s) — %(emails)s email(s) ajouté(s) à la blacklist.",
            leads=len(active_leads),
            emails=len(emails_to_block),
        )
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _("Marqué comme SPAM"),
                'message': msg,
                'type': 'success',
                'sticky': False,
            },
        }

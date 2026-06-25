from datetime import timedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class SalesExportWizard(models.TransientModel):
    _name = 'odooskills.sales.export.wizard'
    _description = "Assistant d'export Excel des ventes par période"

    @api.model
    def _default_date_from(self):
        return fields.Date.context_today(self).replace(day=1)

    date_from = fields.Date(
        string='Du', required=True, default=_default_date_from)
    date_to = fields.Date(
        string='Au', required=True, default=fields.Date.context_today)

    def action_download(self):
        """Construit la synthèse de la période choisie et la télécharge."""
        self.ensure_one()
        if self.date_from > self.date_to:
            raise UserError(_("La date de début doit précéder la date de fin."))

        orders = self.env['sale.order'].search([
            ('state', 'in', ('sale', 'done')),
            ('date_order', '>=', fields.Datetime.to_datetime(self.date_from)),
            # date_to incluse → borne stricte au lendemain.
            ('date_order', '<', fields.Datetime.to_datetime(self.date_to + timedelta(days=1))),
        ])
        title = _('Synthèse des ventes du %s au %s') % (
            self.date_from.strftime('%d/%m/%Y'), self.date_to.strftime('%d/%m/%Y'))
        data = orders._build_orders_xlsx(title=title)
        filename = 'synthese_ventes_%s_%s.xlsx' % (
            self.date_from.strftime('%Y%m%d'), self.date_to.strftime('%Y%m%d'))
        return orders._xlsx_download_action(data, filename)

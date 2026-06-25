import base64
import io
from datetime import timedelta

from odoo import api, fields, models, _

MIMETYPE = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # ------------------------------------------------------------------
    # Constructeur de fichier — partagé par l'assistant, l'action serveur
    # et la tâche planifiée. Une seule source de vérité pour le rendu.
    # ------------------------------------------------------------------
    def _build_orders_xlsx(self, title=None):
        """Construit une synthèse XLSX du CA par produit pour `self`.

        Agrège les lignes de `self` par produit via `_read_group` (SQL) et
        retourne les octets (`bytes`) du fichier. Recordset vide → en-tête seul.
        """
        import xlsxwriter  # vendored par Odoo

        title = title or _('Synthèse des ventes sélectionnées')
        line_domain = [('order_id', 'in', self.ids), ('display_type', '=', False)]
        groups = self.env['sale.order.line']._read_group(
            line_domain, groupby=['product_id'], aggregates=['price_subtotal:sum', '__count'],
        )
        rows = sorted(
            ((product.display_name, count, subtotal)
             for product, subtotal, count in groups),
            key=lambda r: r[2], reverse=True,
        )

        buffer = io.BytesIO()
        workbook = xlsxwriter.Workbook(buffer, {'in_memory': True})
        sheet = workbook.add_worksheet(_('Synthèse'))
        title_fmt = workbook.add_format({
            'bold': True, 'font_size': 13, 'font_color': '#FFFFFF',
            'bg_color': '#1D6F42', 'align': 'left', 'valign': 'vcenter',
        })
        header_fmt = workbook.add_format({
            'bold': True, 'font_color': '#FFFFFF', 'bg_color': '#2E7D54', 'border': 1,
        })
        text_fmt = workbook.add_format({'border': 1})
        int_fmt = workbook.add_format({'num_format': '#,##0', 'border': 1})
        money_fmt = workbook.add_format({'num_format': '#,##0.00\\ €', 'border': 1})
        total_fmt = workbook.add_format({
            'bold': True, 'bg_color': '#E8F3EC', 'num_format': '#,##0.00\\ €', 'border': 1,
        })

        sheet.set_column(0, 0, 42)
        sheet.set_column(1, 1, 12)
        sheet.set_column(2, 2, 18)
        sheet.merge_range(0, 0, 0, 2, title, title_fmt)
        sheet.set_row(0, 22)
        for col, label in enumerate((_('Produit'), _('Nombre'), _('CA HT'))):
            sheet.write(1, col, label, header_fmt)

        row = 2
        total = 0.0
        for name, count, amount in rows:
            sheet.write(row, 0, name, text_fmt)
            sheet.write_number(row, 1, count, int_fmt)
            sheet.write_number(row, 2, amount, money_fmt)
            total += amount
            row += 1
        sheet.write(row, 0, _('Total'), header_fmt)
        sheet.write_blank(row, 1, None, header_fmt)
        sheet.write_number(row, 2, total, total_fmt)

        workbook.close()
        data = buffer.getvalue()
        buffer.close()
        return data

    def _xlsx_download_action(self, data, filename):
        """Crée une pièce jointe binaire et renvoie l'action de téléchargement."""
        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'datas': base64.b64encode(data),
            'type': 'binary',
            'mimetype': MIMETYPE,
        })
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % attachment.id,
            'target': 'self',
        }

    # ------------------------------------------------------------------
    # Cible de l'action serveur (multi-sélection sur la vue liste).
    # ------------------------------------------------------------------
    def action_export_selected_xlsx(self):
        """Exporte les commandes sélectionnées dans la liste."""
        data = self._build_orders_xlsx(title=_('Synthèse — commandes sélectionnées'))
        return self._xlsx_download_action(data, 'synthese_selection.xlsx')

    # ------------------------------------------------------------------
    # Cible de la tâche planifiée (ir.cron) : synthèse du mois écoulé,
    # envoyée par e-mail en pièce jointe.
    # ------------------------------------------------------------------
    @api.model
    def _cron_email_monthly_report(self):
        """Génère la synthèse du mois précédent et l'envoie par e-mail."""
        today = fields.Date.context_today(self)
        first_of_month = today.replace(day=1)
        last_prev = first_of_month - timedelta(days=1)
        first_prev = last_prev.replace(day=1)

        orders = self.search([
            ('state', 'in', ('sale', 'done')),
            ('date_order', '>=', fields.Datetime.to_datetime(first_prev)),
            ('date_order', '<', fields.Datetime.to_datetime(first_of_month)),
        ])
        period = first_prev.strftime('%m/%Y')
        data = orders._build_orders_xlsx(title=_('Synthèse des ventes — %s') % period)

        attachment = self.env['ir.attachment'].create({
            'name': 'synthese_ventes_%s.xlsx' % first_prev.strftime('%Y_%m'),
            'datas': base64.b64encode(data),
            'type': 'binary',
            'mimetype': MIMETYPE,
        })

        recipient = (self.env['ir.config_parameter'].sudo()
                     .get_param('odooskills.monthly_report_email')
                     or self.env.company.email)
        if not recipient:
            return False  # pas de destinataire configuré : on n'envoie rien

        mail = self.env['mail.mail'].create({
            'subject': _('Synthèse des ventes — %s') % period,
            'body_html': _('<p>Bonjour,</p><p>Veuillez trouver ci-joint la synthèse '
                           'des ventes du mois %s.</p>') % period,
            'email_to': recipient,
            'attachment_ids': [(6, 0, attachment.ids)],
        })
        mail.send()
        return True

import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class MailMail(models.Model):
    _inherit = 'mail.mail'

    oski_delivery_alerted = fields.Boolean(
        default=False, copy=False, index=True,
        help="Garde anti-spam : ce mail en échec a déjà déclenché une alerte "
             "de livraison ebook.")


class OskiDeliveryMonitor(models.AbstractModel):
    _name = 'oski.delivery.monitor'
    _description = "Surveillance des échecs de livraison ebook"

    @api.model
    def _cron_alert_failed_deliveries(self):
        """Détecte les emails client tombés en 'exception' (SMTP KO, etc.) et
        prévient l'admin : un acheteur non livré = réclamation + réputation. Large
        volontairement — une livraison peut partir en transactionnel (sale.order)
        OU en masse (mailing.contact, ex. re-livraison). Les exceptions sont rares,
        le bruit est quasi nul. Idempotent via oski_delivery_alerted."""
        Mail = self.env['mail.mail'].sudo()
        failed = Mail.search([
            ('state', '=', 'exception'),
            ('oski_delivery_alerted', '=', False),
        ])
        if not failed:
            return False

        get = self.env['ir.config_parameter'].sudo().get_param
        alert_to = (get('oski_ebook_lifecycle.alert_email')
                    or self.env.company.email
                    or self.env.ref('base.user_admin').email)

        if not alert_to:
            _logger.warning(
                "Échec livraison ebook détecté (%d mail) mais aucun email "
                "d'alerte : configurez oski_ebook_lifecycle.alert_email.",
                len(failed))
            failed.write({'oski_delivery_alerted': True})
            return False

        SaleOrder = self.env['sale.order'].sudo()
        rows = []
        for m in failed:
            ref = ""
            recipient = m.email_to or "?"
            if m.mail_message_id.model == 'sale.order':
                order = SaleOrder.browse(m.mail_message_id.res_id).exists()
                if order:
                    ref = " (commande %s)" % order.name
                    recipient = m.email_to or order.partner_id.email or "?"
            subject = m.mail_message_id.subject or "(sans objet)"
            rows.append(
                "<li><b>%s</b>%s — « %s » — %s<br/>"
                "<small style='color:#888'>%s</small></li>" % (
                    recipient, ref, subject, m.create_date,
                    m.failure_reason or m.failure_type or "raison inconnue"))

        body = (
            "<div style='font-family:Arial,sans-serif;color:#1a1a2e'>"
            "<p>⚠️ <b>%d email(s) client en échec</b> (state=exception). "
            "Ces destinataires n'ont <b>pas reçu leur email</b> — vérifier "
            "s'il s'agit d'une livraison d'ebook :</p>"
            "<ul>%s</ul>"
            "<p>Action : relancer l'envoi (bouton « Renvoyer » sur la commande "
            "ou le mailing, ou corriger le SMTP), puis prévenir le client.</p>"
            "</div>" % (len(failed), "".join(rows)))

        self.env['mail.mail'].sudo().create({
            'subject': "⚠️ Échec envoi email client — %d en attente" % len(failed),
            'email_to': alert_to,
            'body_html': body,
            'auto_delete': False,
            # anti-boucle : si CE mail d'alerte échoue à son tour, il ne doit pas
            # se ré-alerter lui-même au prochain passage du cron.
            'oski_delivery_alerted': True,
        }).send(raise_exception=False)

        failed.write({'oski_delivery_alerted': True})
        _logger.warning(
            "Alerte échec livraison ebook envoyée à %s (%d mail).",
            alert_to, len(failed))
        return True

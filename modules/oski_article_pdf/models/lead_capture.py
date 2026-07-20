import logging

from odoo import api, models

_logger = logging.getLogger(__name__)


class OskiLeadCapture(models.AbstractModel):
    _inherit = 'oski.lead.capture'

    @api.model
    def _oski_capture_lead(self, email, consent, source, blog_post=None,
                           client_ip=None):
        result = super()._oski_capture_lead(
            email, consent, source, blog_post, client_ip=client_ip)
        if result.get('ok') and result.get('pdf_url') and blog_post:
            self._oski_send_pdf_mail(email, blog_post, result['pdf_url'])
        return result

    @api.model
    def _oski_send_pdf_mail(self, email, blog_post, pdf_url):
        """Copie par email du lien de téléchargement. Le téléchargement
        immédiat reste la voie principale : un échec d'envoi ne doit jamais
        casser la livraison.

        Le mail.mail est créé et rendu EN REQUÊTE
        (`send_mail(force_send=False)`), dans la même transaction que la
        capture : c'est ce qui permet au commit normal de la requête HTTP de
        le persister réellement, avec son mail.message associé. Écrire
        depuis un callback `cr.postcommit` ne suffirait PAS : Cursor.commit()
        exécute postcommit.run() sur le curseur de requête encore ouvert
        (odoo/sql_db.py:555), puis la couche HTTP referme ensuite ce même
        curseur (odoo/http.py:2270-2272), et Cursor._close() appelle
        rollback() (odoo/sql_db.py:536) — tout ce qui aurait été écrit
        depuis ce callback serait donc systématiquement perdu, alors même
        que l'email est réellement parti.

        Seul l'envoi SMTP proprement dit reste différé, via le pattern
        canonique `mail.mail.send_after_commit()`
        (odoo/addons/mail/models/mail_mail.py:668-688) : celui-ci ouvre,
        dans un callback post-commit, un NOUVEAU curseur de registre qu'il
        committe lui-même à la sortie — donc bien en dehors du curseur de
        la requête. Un serveur SMTP qui ne répond pas ne retarde ainsi
        jamais la réponse JSON de capture (et donc le téléchargement, qui
        n'attend que cette réponse)."""
        template = self.env.ref('oski_article_pdf.mail_pdf_delivery',
                                raise_if_not_found=False)
        if not template:
            return
        base = self.env['ir.config_parameter'].sudo().get_param(
            'web.base.url', 'https://odooskills.com').rstrip('/')
        absolute = pdf_url if pdf_url.startswith('http') else base + pdf_url

        try:
            mail_id = template.sudo().with_context(pdf_url=absolute).send_mail(
                blog_post.id, force_send=False,
                email_values={'email_to': email})
            self.env['mail.mail'].sudo().browse(mail_id).send_after_commit()
        except Exception:
            _logger.exception("Échec d'envoi du guide PDF à %s", email)

from lxml import html as lxml_html
from markupsafe import Markup

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import email_split, format_datetime, formataddr

SIGNATURE_ATTRIBUTE = 'data-oski-signature'


class OskiMailDraft(models.Model):
    _name = 'oski.mail.draft'
    _description = 'Brouillon de message'
    _order = 'write_date desc, id desc'
    _rec_name = 'subject'

    mailbox_id = fields.Many2one(
        'oski.mailbox', string='Envoyer depuis', required=True,
        default=lambda self: self.env['oski.mailbox'].search([], limit=1))
    inbox_id = fields.Many2one(
        'oski.mail.inbox', string='En réponse à', ondelete='set null', readonly=True)
    email_to = fields.Char(string='À', required=True)
    # Pas d'"email_cc" : il n'existe pas de canal Cc côté mail_thread
    # sans créer de partenaire (outgoing_email_to est seul disponible
    # sans AccessError, voir action_send) ; un champ appelé "Copie" aurait
    # promis un en-tête Cc jamais envoyé. Ces adresses sont donc fondues
    # dans les destinataires principaux, et le champ le dit.
    email_more_to = fields.Char(
        string='Autres destinataires',
        help="Adresses supplémentaires, séparées par des virgules. Ajoutées "
             "aux destinataires principaux : il n'existe pas de copie "
             "distincte sans créer de partenaire pour chacune.")
    subject = fields.Char(string='Sujet', required=True)
    # sanitize_attributes=False : le sanitizer HTML par défaut de l'ORM ne
    # garde qu'une liste blanche d'attributs qui n'inclut pas
    # data-oski-signature, ce qui effacerait le marqueur de signature à
    # chaque écriture. Le désactiver ne réintroduit pas de danger : les
    # balises restent filtrées (sanitize_tags reste actif), seule la liste
    # blanche d'attributs s'élargit — c'est le même compromis que celui du
    # corps natif de mail.message pour ses propres marqueurs data-o-mail-*.
    body_html = fields.Html(string='Message', sanitize=True, sanitize_attributes=False)
    attachment_ids = fields.Many2many('ir.attachment', string='Pièces jointes')
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('sent', 'Envoyé'),
    ], string='État', default='draft', readonly=True, index=True)
    date_sent = fields.Datetime(string='Envoyé le', readonly=True)
    mail_message_id = fields.Many2one(
        'mail.message', string='Message produit', readonly=True, ondelete='set null')

    def write(self, vals):
        if set(vals) - {'state', 'date_sent', 'mail_message_id', 'inbox_id'}:
            for draft in self:
                if draft.state == 'sent':
                    raise UserError(_(
                        "Ce message a été envoyé le %s : il ne peut plus être modifié.",
                        format_datetime(self.env, draft.date_sent)))
        return super().write(vals)

    # ------------------------------------------------------------------
    # Signature
    # ------------------------------------------------------------------
    @api.model
    def _signature_block(self, mailbox):
        """Bloc de signature marqué, prêt à être inséré dans un corps."""
        raw = (mailbox.signature or '').strip() or (self.env.user.signature or '').strip()
        if not raw:
            return Markup()
        return Markup('<div %s="1">%s</div>') % (
            Markup(SIGNATURE_ATTRIBUTE), Markup(raw))

    @staticmethod
    def _detach_node(node):
        """Retire un nœud lxml sans perdre le texte qui le suivait.

        node.getparent().remove(node) tout court jette aussi node.tail : si
        un utilisateur tape juste après la signature dans l'éditeur, ce
        texte est le tail du nœud de signature, et un simple remove() le
        ferait disparaître au premier changement d'expéditeur."""
        parent = node.getparent()
        tail = node.tail or ''
        previous = node.getprevious()
        if previous is not None:
            previous.tail = (previous.tail or '') + tail
        else:
            parent.text = (parent.text or '') + tail
        parent.remove(node)

    @staticmethod
    def _fragment_to_string(fragment):
        rebuilt = fragment.text or ''
        rebuilt += ''.join(
            lxml_html.tostring(child, encoding='unicode') for child in fragment)
        return rebuilt

    @api.model
    def _strip_signature(self, body):
        """Retire tout bloc de signature d'un corps, quel que soit son contenu.

        lxml et non une expression régulière : une signature contenant un
        <div> ferait dérailler tout motif non gourmand, et couperait le corps
        au mauvais endroit."""
        if not body:
            return ''
        fragment = lxml_html.fragment_fromstring(body, create_parent='div')
        for node in fragment.xpath('//*[@%s]' % SIGNATURE_ATTRIBUTE):
            self._detach_node(node)
        return self._fragment_to_string(fragment)

    def _swap_signature(self, body, mailbox):
        """Remplace la signature en place plutôt que de la déplacer.

        Rebâtir le corps en préfixant systématiquement le nouveau bloc — ce
        que ferait _strip_signature() suivi d'une concaténation — ferait
        remonter la signature au-dessus du message à chaque changement
        d'expéditeur sur un brouillon déjà composé (une réponse, typiquement,
        où _reply_body() place la signature avant la citation, pas en tête
        du corps final). Le nœud marqué existant est donc repéré et
        substitué à sa place ; seule une signature absente retombe sur un
        préfixe, faute d'endroit où s'ancrer."""
        self.ensure_one()
        new_block = self._signature_block(mailbox)
        if not body:
            return new_block
        fragment = lxml_html.fragment_fromstring(body, create_parent='div')
        marked = fragment.xpath('//*[@%s]' % SIGNATURE_ATTRIBUTE)
        if not marked:
            stripped = self._fragment_to_string(fragment)
            return new_block + Markup(stripped)
        anchor, extra_nodes = marked[0], marked[1:]
        if new_block:
            new_node = lxml_html.fragment_fromstring(str(new_block))
            new_node.tail = anchor.tail
            anchor.getparent().replace(anchor, new_node)
        else:
            self._detach_node(anchor)
        for node in extra_nodes:
            self._detach_node(node)
        return Markup(self._fragment_to_string(fragment))

    @api.onchange('mailbox_id')
    def _onchange_mailbox_signature(self):
        for draft in self:
            draft.body_html = draft._swap_signature(draft.body_html, draft.mailbox_id)

    # ------------------------------------------------------------------
    # Envoi
    # ------------------------------------------------------------------
    def _ensure_thread(self):
        """Retourne la fiche qui porte le fil ; un message neuf en crée une.

        Faire porter le fil par une fiche d'email plutôt que par le brouillon
        permet à la réponse du destinataire de rejoindre la conversation par
        In-Reply-To, au lieu d'ouvrir un fil orphelin."""
        self.ensure_one()
        if self.inbox_id:
            return self.inbox_id
        record = self.env['oski.mail.inbox'].create({
            'subject': self.subject,
            'email_from': self.mailbox_id.email,
            'mailbox_id': self.mailbox_id.id,
            'body_html': self.body_html,
            'date_received': fields.Datetime.now(),
            'state': 'answered',
        })
        self.inbox_id = record
        return record

    def _outgoing_emails(self):
        self.ensure_one()
        addresses = email_split(self.email_to or '') + email_split(self.email_more_to or '')
        return ','.join(dict.fromkeys(addresses))

    def action_send(self):
        self.ensure_one()
        if self.state == 'sent':
            raise UserError(_("Ce message a déjà été envoyé."))
        mailbox = self.mailbox_id
        recipients = self._outgoing_emails()
        if not recipients:
            raise UserError(_("Aucun destinataire valide."))

        thread = self._ensure_thread()
        message = thread.with_context(oski_reply_mailbox_id=mailbox.id).message_post(
            body=Markup(self.body_html or ''),
            subject=self.subject,
            message_type='comment',
            subtype_xmlid='mail.mt_comment',
            email_from=formataddr((self.env.user.name, mailbox.email)),
            author_id=self.env.user.partner_id.id,
            outgoing_email_to=recipients,
            attachment_ids=self.attachment_ids.ids,
            # sudo() : mail_server_id porte groups="base.group_system" côté vue
            # (le mot de passe SMTP qu'il implique n'est pas affaire de tout le
            # monde) ; un Manager non-système doit pouvoir envoyer sans lire le
            # champ lui-même.
            mail_server_id=mailbox.sudo().mail_server_id.id or False,
        )
        self.write({
            'state': 'sent',
            'date_sent': fields.Datetime.now(),
            'mail_message_id': message.id,
        })
        return {'type': 'ir.actions.act_window_close'}

    def action_open_original(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'oski.mail.inbox',
            'view_mode': 'form',
            'res_id': self.inbox_id.id,
        }

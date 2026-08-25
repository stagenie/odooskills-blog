from odoo import api, fields, models
from odoo.tools import email_normalize


class OskiMailBlocklist(models.Model):
    _name = 'oski.mail.blocklist'
    _description = 'Adresse bloquée'
    _order = 'blocked_date desc, id desc'
    _rec_name = 'email'

    email = fields.Char(string='Adresse', required=True, index=True)
    origin_inbox_id = fields.Many2one(
        'oski.mail.inbox', string='Email d\'origine', ondelete='set null', readonly=True)
    active = fields.Boolean(default=True)
    blocked_uid = fields.Many2one(
        'res.users', string='Bloquée par', readonly=True,
        default=lambda self: self.env.user)
    blocked_date = fields.Datetime(
        string='Bloquée le', readonly=True, default=fields.Datetime.now)

    _email_unique = models.Constraint(
        'UNIQUE (email)', "Cette adresse est déjà dans la liste de blocage.")

    @api.model
    def _normalise(self, value):
        return email_normalize(value or '') or (value or '').strip().lower()

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('email'):
                vals['email'] = self._normalise(vals['email'])
        return super().create(vals_list)

    def write(self, vals):
        if vals.get('email'):
            vals['email'] = self._normalise(vals['email'])
        return super().write(vals)

    @api.model
    def _is_blocked(self, email_from):
        normalised = email_normalize(email_from or '')
        if not normalised:
            return False
        # sudo : la passerelle entrante s'exécute sans utilisateur applicatif.
        return bool(self.sudo().search_count([('email', '=', normalised)]))

    @api.model
    def _block(self, email_from, origin_inbox=None):
        """Bloque une adresse, en réactivant la ligne archivée s'il y en a une.

        La contrainte UNIQUE porte sur toutes les lignes, archivées comprises :
        recréer après un déblocage échouerait."""
        normalised = email_normalize(email_from or '')
        if not normalised:
            return self.browse()
        existing = self.sudo().with_context(active_test=False).search(
            [('email', '=', normalised)], limit=1)
        if existing:
            # sudo borné à la réactivation : bloquer est un geste d'utilisateur,
            # débloquer reste réservé au Manager par les droits d'accès.
            if not existing.active:
                existing.write({'active': True})
            return existing
        return self.create({
            'email': normalised,
            'origin_inbox_id': origin_inbox.id if origin_inbox else False,
        })

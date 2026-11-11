from odoo import api, fields, models
from odoo.exceptions import AccessError


class OskiDemandeType(models.Model):
    _name = 'oski.demande.type'
    _description = "Type de demande"
    _order = 'name'

    name = fields.Char("Type", required=True, translate=True)


class OskiDemande(models.Model):
    _name = 'oski.demande'
    _description = "Demande interne"
    _order = 'id desc'

    name = fields.Char("Objet", required=True)
    type_id = fields.Many2one('oski.demande.type', string="Type")
    user_id = fields.Many2one(
        'res.users', string="Demandeur", required=True, index=True,
        default=lambda self: self.env.user)
    company_id = fields.Many2one(
        'res.company', string="Société", required=True, index=True,
        default=lambda self: self.env.company)
    montant = fields.Float("Montant")
    state = fields.Selection(
        [('draft', "Brouillon"), ('submitted', "Soumise"), ('approved', "Approuvée")],
        string="État", default='draft', required=True)
    note = fields.Text("Note")

    def write(self, vals):
        # Le bouton « Approuver » est masqué aux demandeurs, mais la vue n'est pas une
        # sécurité : un appel RPC (write ou action_approve) passe outre. Le demandeur a le
        # droit d'écriture sur SES demandes ; ce droit ne doit pas suffire pour approuver.
        if vals.get('state') == 'approved' and not self.env.su \
                and not self.env.user.has_group('oski_demandes_droits.group_demande_valideur'):
            raise AccessError("Seul un valideur peut approuver une demande.")
        return super().write(vals)

    def action_submit(self):
        self.write({'state': 'submitted'})

    def action_approve(self):
        self.write({'state': 'approved'})

    @api.model
    def _stats_publiques(self):
        """Nombre de demandes par état, sans rien d'autre : seul usage public."""
        groupes = self.sudo()._read_group([], ['state'], ['__count'])
        return {state: count for state, count in groupes}

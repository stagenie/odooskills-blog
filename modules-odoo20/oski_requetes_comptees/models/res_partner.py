from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    oski_nb_commandes = fields.Integer('Commandes confirmées', compute='_compute_oski_nb_commandes')

    def _compute_oski_nb_commandes(self):
        # une seule requête GROUP BY pour tous les contacts du lot
        groupes = self.env['sale.order']._read_group(
            [('partner_id', 'in', self.ids), ('state', '=', 'sale')],
            groupby=['partner_id'], aggregates=['__count'])
        nb = {partner.id: count for partner, count in groupes}
        for partner in self:
            partner.oski_nb_commandes = nb.get(partner.id, 0)

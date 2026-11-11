from odoo import api, fields, models
from odoo.fields import Domain


class OskiParcMateriel(models.Model):
    _name = 'oski.parc.materiel'
    _description = 'Matériel prêté'
    _rec_names_search = ('name', 'numero_serie')

    name = fields.Char('Désignation', required=True)
    numero_serie = fields.Char('Numéro de série')
    reference = fields.Char('Référence', compute='_compute_reference', store=True)
    partner_id = fields.Many2one('res.partner', 'Prêté à')
    date_pret = fields.Date('Date du prêt')
    company_id = fields.Many2one('res.company', 'Société', default=lambda self: self.env.company)

    @api.depends('numero_serie', 'company_id.oski_parc_prefixe')
    def _compute_reference(self):
        for rec in self:
            prefixe = rec.company_id.oski_parc_prefixe or 'MAT'
            rec.reference = f"{prefixe}/{rec.numero_serie}" if rec.numero_serie else False

    @api.model
    def _domaine_en_pret(self, partner=None):
        domaine = Domain('partner_id', '!=', False)
        if partner:
            domaine &= Domain('partner_id', '=', partner.id)
        return domaine

    def action_voir_en_pret(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Matériel en prêt',
            'res_model': self._name,
            'view_mode': 'list,form',
            'domain': self._domaine_en_pret(),
        }

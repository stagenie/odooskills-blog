from odoo import api, fields, models


class OskiEbook(models.Model):
    _name = 'oski.ebook'
    _description = 'OdooSkills Ebook (lifecycle)'
    _rec_name = 'name'
    _order = 'code'

    code = fields.Char(string='Code', required=True, help="Ex. E1, E2, E4…")
    name = fields.Char(string='Nom', required=True)
    partner_category_id = fields.Many2one(
        'res.partner.category', string='Catégorie client', required=True,
        help="Tag posé sur le partner à l'achat de cet ebook.")
    extract_list_id = fields.Many2one(
        'mailing.list', string='Liste extrait',
        help="Liste de nurture « Extrait » à passer en opt_out une fois l'ebook acheté.")
    active = fields.Boolean(default=True)

    _unique_code = models.Constraint('unique(code)', "Le code ebook doit être unique.")

    @api.depends('code', 'name')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = '%s — %s' % (rec.code or '', rec.name or '')

from odoo import api, fields, models


class OskiWidgetDemo(models.Model):
    _name = 'oski.widget.demo'
    _description = 'Démonstration des widgets de champ'
    _order = 'sequence, id'

    name = fields.Char('Nom', required=True)
    sequence = fields.Integer('Séquence', default=10)

    # Sélections et états
    state = fields.Selection(
        [('draft', 'Brouillon'), ('open', 'En cours'), ('done', 'Terminé'), ('cancel', 'Annulé')],
        string='Étape', default='draft', required=True)
    priority = fields.Selection(
        [('0', 'Normale'), ('1', 'Haute'), ('2', 'Très haute'), ('3', 'Urgente')],
        string='Priorité', default='0')
    channel = fields.Selection(
        [('email', 'Courriel'), ('phone', 'Téléphone'), ('visit', 'Visite')],
        string='Canal', default='email')
    category_id = fields.Many2one('res.partner.category', string='Catégorie principale')

    # Relations
    partner_id = fields.Many2one('res.partner', string='Contact')
    tag_ids = fields.Many2many('res.partner.category', string='Étiquettes')
    partner_ids = fields.Many2many(
        'res.partner', 'oski_widget_demo_partner_rel', 'demo_id', 'partner_id', string='Participants')
    attachment_ids = fields.Many2many('ir.attachment', string='Pièces jointes')
    tag_count = fields.Integer('Nombre d’étiquettes', compute='_compute_tag_count')

    # Nombres
    progress = fields.Float('Avancement')
    target = fields.Integer('Objectif', default=100)
    rate = fields.Float('Taux de remise')
    pie = fields.Float('Couverture')
    duration = fields.Float('Durée')
    currency_id = fields.Many2one(
        'res.currency', string='Devise', default=lambda self: self.env.company.currency_id)
    amount = fields.Monetary('Montant', currency_field='currency_id')
    color = fields.Integer('Couleur')
    color_hex = fields.Char('Couleur (hexadécimal)')

    # Booléens
    is_active = fields.Boolean('Actif', default=True)
    is_favorite = fields.Boolean('Favori')

    # Textes, liens, dates
    website = fields.Char('Site web')
    email = fields.Char('Courriel')
    phone = fields.Char('Téléphone')
    reference_code = fields.Char('Code de référence')
    partner_domain = fields.Char('Filtre de contacts', default='[]')
    deadline = fields.Date('Échéance')
    date_start = fields.Date('Début')
    date_end = fields.Date('Fin')
    image = fields.Image('Image', max_width=512, max_height=512)

    @api.depends('tag_ids')
    def _compute_tag_count(self):
        for rec in self:
            rec.tag_count = len(rec.tag_ids)

    def action_open_tags(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('Étiquettes'),
            'res_model': 'res.partner.category',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.tag_ids.ids)],
        }

from odoo import fields, models


class MigrationDemoItem(models.Model):
    """Item démo pour illustrer une migration v18 → v19 minor-bump.

    État v19.0.1.1.0 (post-migration) :
    - champ ``state`` (renommé depuis ``legacy_status``)
    - valeurs ``'confirmed'``/``'cancelled'`` (renommées depuis ``'confirm'``/``'cancel'``)
    - champ ``user_ids`` (renommé depuis ``legacy_user_ids``)
    """

    _name = 'mig.demo.item'
    _description = 'Migration demo item'

    name = fields.Char(required=True)
    state = fields.Selection(
        [
            ('draft', 'Brouillon'),
            ('confirmed', 'Confirmé'),
            ('cancelled', 'Annulé'),
        ],
        default='draft',
        required=True,
    )
    user_ids = fields.Many2many('res.users', string='Responsables')
    note = fields.Text()

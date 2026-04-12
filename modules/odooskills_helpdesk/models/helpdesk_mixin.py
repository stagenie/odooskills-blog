from odoo import models, fields


class HelpdeskMixin(models.AbstractModel):
    """Mixin réutilisable : pas de table en base, uniquement des champs
    et méthodes injectés dans les modèles qui l'héritent.

    Usage : ajouter _inherit = 'odooskills.helpdesk.mixin' sur le modèle cible.
    """
    _name = 'odooskills.helpdesk.mixin'
    _description = 'Mixin helpdesk — champs communs'

    active = fields.Boolean(default=True)
    priority = fields.Selection(
        selection=[
            ('0', 'Normale'),
            ('1', 'Haute'),
            ('2', 'Urgente'),
        ],
        default='0',
    )

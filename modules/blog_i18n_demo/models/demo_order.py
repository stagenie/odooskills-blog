from odoo import _, api, fields, models
from odoo.exceptions import UserError


class DemoOrder(models.Model):
    _name = 'blog.i18n.order'
    _description = "Commande de démonstration"  # extrait dans le .pot

    name = fields.Char(string="Référence", required=True, default="Brouillon")
    state = fields.Selection(
        selection=[
            ('draft', "Brouillon"),
            ('confirmed', "Confirmée"),
        ],
        string="État",
        default='draft',
    )

    def action_confirm(self):
        self.ensure_one()
        if self.state == 'confirmed':
            # Chaîne marquée pour la traduction avec la fonction _()
            raise UserError(_("Cette commande est déjà confirmée."))
        self.state = 'confirmed'
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': _("Commande confirmée avec succès."),
                'type': 'success',
            },
        }

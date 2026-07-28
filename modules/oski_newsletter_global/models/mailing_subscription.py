from odoo import api, models


class MailingSubscription(models.Model):
    _inherit = 'mailing.subscription'

    @api.model_create_multi
    def create(self, vals_list):
        """Rattrape les contacts pré-existants inscrits à un segment.

        Le hook sur `mailing.contact.create` ne couvre que les nouveaux venus.
        Un contact déjà en base que l'on ajoute à « Prospects » doit lui aussi
        rejoindre la Globale.

        Les souscriptions à la Globale elle-même sont écartées : sans ce filtre,
        `_oski_ensure_global_list` rappellerait `create` en boucle.
        """
        subscriptions = super().create(vals_list)
        lst = self.env['mailing.contact']._oski_global_list()
        if not lst:
            return subscriptions
        others = subscriptions.filtered(lambda s: s.list_id.id != lst.id)
        if others:
            others.contact_id.sudo()._oski_ensure_global_list()
        return subscriptions

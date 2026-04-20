from odoo import models


class IrWebsocket(models.AbstractModel):
    """T27 — Autorisation du canal bus personnalisé 'odooskills.sla'.

    Sans cette surcharge, `bus_service.addChannel('odooskills.sla')` côté
    client est silencieusement ignoré par le serveur : le canal demandé
    n'est pas dans la liste autorisée construite par `_build_bus_channel_list`.

    Pattern copié de `odoo/addons/im_livechat/models/ir_websocket.py`.
    """

    _inherit = 'ir.websocket'

    def _build_bus_channel_list(self, channels):
        """Ajoute le canal 'odooskills.sla' pour tout utilisateur authentifié.

        On ajoute systématiquement le canal pour tous les utilisateurs internes
        (non-public). Approche simple et pédagogique : une ligne serveur,
        une ligne client (`addChannel`), démo spectaculaire en temps réel.

        En production, restreindre à un groupe précis (ex. base.group_user)
        pour limiter l'exposition du canal.
        """
        channels = list(channels)  # ne pas altérer la liste originale

        if self.env.user and not self.env.user._is_public():
            # Ajouter systématiquement le canal SLA pour les users connectés.
            # Le client appelle addChannel('odooskills.sla') — le serveur
            # doit l'inclure ici pour que le WebSocket l'accepte.
            if 'odooskills.sla' not in channels:
                channels.append('odooskills.sla')

        return super()._build_bus_channel_list(channels)

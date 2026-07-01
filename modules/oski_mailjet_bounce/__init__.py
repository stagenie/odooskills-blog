import secrets

from . import controllers


def post_init_hook(env):
    """Génère un token secret pour l'URL du webhook s'il n'existe pas déjà."""
    icp = env['ir.config_parameter'].sudo()
    if not icp.get_param('oski.mailjet_webhook_token'):
        icp.set_param('oski.mailjet_webhook_token', secrets.token_urlsafe(24))

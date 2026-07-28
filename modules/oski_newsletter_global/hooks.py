import logging

_logger = logging.getLogger(__name__)


def post_init(env):
    """Fait entrer dans la Globale les contacts créés avant l'installation.

    Idempotent : `_oski_ensure_global_list` ignore ceux qui y sont déjà, opt_out
    compris.
    """
    Contact = env['mailing.contact']
    lst = Contact._oski_global_list()
    if not lst:
        _logger.warning('post_init: liste globale introuvable, rattrapage sauté')
        return
    contacts = Contact.search([])
    before = env['mailing.subscription'].search_count([('list_id', '=', lst.id)])
    contacts._oski_ensure_global_list()
    after = env['mailing.subscription'].search_count([('list_id', '=', lst.id)])
    _logger.info(
        'post_init: Newsletter Globale %s -> %s souscriptions (%s contacts en base)',
        before, after, len(contacts))

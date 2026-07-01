{
    'name': 'OdooSkills - Webhook Bounce Mailjet',
    'version': '19.0.1.0.0',
    'category': 'Marketing/Email Marketing',
    'summary': "Réception des événements Mailjet (bounce/blocked/spam/unsub) → blacklist auto",
    'description': """
OdooSkills - Webhook Bounce Mailjet
===================================

Expose un endpoint public sécurisé par token qui reçoit les événements
Mailjet (Event API) et blackliste automatiquement les adresses mortes :

- ``blocked``, ``spam``, ``unsub``  → blacklist
- ``bounce`` avec ``hard_bounce``/``blocked`` → blacklist
- soft bounce (temporaire) → ignoré (log seulement)

URL du webhook : ``https://<domaine>/mailjet/events/<token>``
Le token est généré à l'installation dans le paramètre système
``oski.mailjet_webhook_token`` (Mailjet ne signe pas ses payloads,
le secret dans l'URL sert d'authentification).

À configurer côté Mailjet : Compte > Event notifications (triggers),
coller l'URL pour bounce / blocked / spam / unsub.
    """,
    'author': 'ADICOPS',
    'website': 'https://odooskills.com',
    'license': 'LGPL-3',
    'depends': ['mail'],
    'data': [],
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'application': False,
    'auto_install': False,
}

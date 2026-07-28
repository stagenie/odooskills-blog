{
    'name': 'OdooSkills - Newsletter Globale unique',
    'version': '19.0.1.0.0',
    'category': 'Marketing/Email Marketing',
    'summary': "Tout contact newsletter entre automatiquement dans la Newsletter Globale",
    'description': """
Newsletter Globale = référentiel unique des contacts OdooSkills
================================================================

Les inscriptions arrivaient par des portes différentes (popup lead magnet,
téléchargement de PDF, snippet newsletter du site, extraits d'ebook, imports)
et chacune poussait vers SA liste. Résultat : aucune liste ne contenait tout
le monde, et un envoi « à tous » obligeait à cocher plusieurs listes en
espérant que le dédoublonnage suive.

Ce module pose une règle unique : **tout contact de mailing appartient à la
Newsletter Globale**, quelle que soit la porte d'entrée. Les autres listes
restent des segments.

Ce module ne retire jamais personne de la Globale : filtrer les clients ou
tout autre sous-ensemble se fait au moment de l'envoi, sur les étiquettes.

Désinscription respectée : si un contact a déjà une souscription à la Globale
avec opt_out, elle n'est pas recréée ni réactivée. En revanche un retrait pur
et simple de la liste est annulé — pour cesser d'écrire à quelqu'un, on pose
opt_out ou la liste noire, on ne le sort pas du référentiel.
""",
    'author': 'ADICOPS',
    'website': 'https://odooskills.com',
    'license': 'LGPL-3',
    'depends': ['mass_mailing'],
    'data': [],
    'post_init_hook': 'post_init',
    'installable': True,
    'application': False,
    'auto_install': True,
}

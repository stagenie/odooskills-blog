"""Reprise de l'existant — §9 de la spec, ids de la base de production Odooskills.

Blog 1 = Fonctionnel Odoo, blog 2 = Développement Odoo. L'ordre de la liste est
l'ordre des séries sur /parcours. Articles laissés indépendants : 90 (dév), 92 (fonc)."""

BLOG_FONC = 1
BLOG_DEV = 2

SERIES = [
    # ---- Développement ------------------------------------------------------
    {
        'name': "Parcours Fondamentaux du développeur", 'blog': BLOG_DEV, 'version': '19.0',
        'audience': "Débutant · développeur", 'tag': None,
        'description': "De l'installation d'Odoo 19 aux contrôleurs HTTP : 23 étapes pour écrire "
                       "vos premiers modules, chaque notion s'appuyant sur la précédente.",
        'blocks': [
            ("Installation", [50, 52, 53]),
            ("Environnement dev", [54, 55, 56, 57]),
            ("Framework ORM", [59, 60, 61, 62, 63, 64, 65, 66]),
            ("Interface utilisateur", [67, 68, 69, 70]),
            ("Rapports et automatisations", [71, 72, 73, 74]),
        ],
    },
    {
        'name': "Aller plus loin en v19", 'blog': BLOG_DEV, 'version': '19.0',
        'audience': "Confirmé · développeur", 'tag': None,
        'description': "Tests automatisés, migration de la 18 à la 19, composants OWL et temps réel "
                       "avec bus.bus : les sujets qui suivent les fondamentaux.",
        'blocks': [(None, [105, 106, 107, 108, 109])],
    },
    {
        'name': "L'environnement du développeur", 'blog': BLOG_DEV, 'version': None,
        'audience': "Débutant · développeur", 'tag': 'serie-tech-s01-sandbox',
        'description': "Linux, Git, Bash, odoo-bin shell et PostgreSQL : les outils du quotidien, "
                       "valables quelle que soit la version d'Odoo.",
        'blocks': [(None, [116, 117, 118, 119, 120])],
    },
    {
        'name': "Infrastructure emailing", 'blog': BLOG_DEV, 'version': '19.0',
        'audience': "Intermédiaire · développeur et intégrateur", 'tag': None,
        'description': "Authentification des envois, serveurs sortants et entrants, mail.thread, modèles "
                       "d'email et diffusion de masse : la messagerie d'Odoo couche par couche.",
        'blocks': [(None, [121, 123, 125, 130, 132, 133, 135, 138, 139, 140, 141, 142, 143, 144])],
    },
    {
        'name': "Rapports Excel", 'blog': BLOG_DEV, 'version': '19.0',
        'audience': "Intermédiaire · développeur", 'tag': None,
        'description': "Du premier fichier XLSX natif à l'export industrialisé : mise en forme, "
                       "feuilles multiples, graphiques et gros volumes.",
        'blocks': [(None, [145, 149, 150, 151, 152, 153])],
    },
    {
        'name': "Rapports PDF", 'blog': BLOG_DEV, 'version': '19.0',
        'audience': "Intermédiaire · développeur", 'tag': None,
        'description': "Personnaliser un rapport existant, en créer un de zéro, gérer les sorties "
                       "d'impression, la mise en page et les rapports dynamiques.",
        'blocks': [(None, [160, 161, 162, 163, 164])],
    },
    {
        'name': "Traduire Odoo (dev)", 'blog': BLOG_DEV, 'version': '19.0',
        'audience': "Intermédiaire · développeur", 'tag': None,
        'description': "Ajouter une langue et traduire l'interface, puis traduire votre propre module "
                       "vers l'arabe.",
        'blocks': [(None, [165, 166])],
    },
    {
        'name': "Licences et distribution", 'blog': BLOG_DEV, 'version': '19.0',
        'audience': "Intermédiaire · développeur", 'tag': 'serie-tech-s02-licences',
        'description': "Choisir la licence de votre module, comprendre le manifeste et publier "
                       "sur l'Odoo Apps Store.",
        'blocks': [(None, [169, 170, 171])],
    },
    # ---- Fonctionnel --------------------------------------------------------
    {
        'name': "Fondations Inventaire", 'blog': BLOG_FONC, 'version': '19.0',
        'audience': "Débutant · utilisateur métier", 'tag': None,
        'description': "Entrepôt et stock initial, unités de mesure, lots et numéros de série, "
                       "routes multi-étapes.",
        'blocks': [(None, [40, 41, 42, 43])],
    },
    {
        'name': "Acheter et vendre", 'blog': BLOG_FONC, 'version': '19.0',
        'audience': "Débutant · utilisateur métier", 'tag': None,
        'description': "Achats, ventes et CRM : le cycle commercial de la commande fournisseur "
                       "à la facture client.",
        'blocks': [(None, [44, 45, 46])],
    },
    {
        'name': "Comptabilité et production", 'blog': BLOG_FONC, 'version': '19.0',
        'audience': "Débutant · utilisateur métier", 'tag': None,
        'description': "Plan comptable et taxes, facturation et paiements, nomenclatures "
                       "et ordres de fabrication.",
        'blocks': [(None, [47, 48, 49, 51])],
    },
    {
        'name': "Ressources humaines", 'blog': BLOG_FONC, 'version': '19.0',
        'audience': "Débutant · utilisateur métier", 'tag': None,
        'description': "Employés et départements, recrutement, congés et temps de présence.",
        'blocks': [(None, [58, 75, 76])],
    },
    {
        'name': "Site web, eCommerce et engagement", 'blog': BLOG_FONC, 'version': '19.0',
        'audience': "Débutant · utilisateur métier", 'tag': None,
        'description': "Site vitrine, blog et forum, boutique en ligne, eLearning, événements "
                       "et sondages.",
        'blocks': [(None, [77, 78, 79, 80, 81, 82])],
    },
    {
        'name': "Marketing et communication", 'blog': BLOG_FONC, 'version': '19.0',
        'audience': "Débutant · utilisateur métier", 'tag': None,
        'description': "Email et SMS marketing, automatisation des campagnes, scoring et "
                       "qualification des leads.",
        'blocks': [(None, [83, 84, 85, 86])],
    },
    {
        'name': "Point de vente et retail", 'blog': BLOG_FONC, 'version': '19.0',
        'audience': "Débutant · utilisateur métier", 'tag': None,
        'description': "Installer le point de vente, encaisser au quotidien, gérer le catalogue, "
                       "les variantes et les promotions en caisse.",
        'blocks': [(None, [87, 88, 89])],
    },
    {
        'name': "Maîtriser les achats et approvisionnements", 'blog': BLOG_FONC, 'version': '19.0',
        'audience': "Intermédiaire · acheteur et gestionnaire de stock", 'tag': None,
        'description': "Contrats-cadres, frais d'import, valorisation du stock et planification "
                       "des approvisionnements, en quatre parties.",
        'blocks': [(None, [95, 96, 99, 100])],
    },
    {
        'name': "Configurateur produit", 'blog': BLOG_FONC, 'version': '19.0',
        'audience': "Intermédiaire · utilisateur métier", 'tag': None,
        'description': "Variantes et prix par variante, saisie en grille, stock différencié "
                       "par variante.",
        'blocks': [(None, [97, 101, 102])],
    },
    {
        'name': "Revenue management", 'blog': BLOG_FONC, 'version': '19.0',
        'audience': "Intermédiaire · utilisateur métier", 'tag': None,
        'description': "Promotions multicanal, listes de prix par segment de clientèle, fidélité "
                       "et cartes-cadeaux.",
        'blocks': [(None, [98, 103, 104])],
    },
    {
        'name': "Gestion de projet et analytique", 'blog': BLOG_FONC, 'version': '19.0',
        'audience': "Intermédiaire · chef de projet", 'tag': 'serie-fonc-s11-projet',
        'description': "Projets et tâches, dépendances, feuilles de temps, comptabilité analytique "
                       "et rentabilité.",
        'blocks': [(None, [111, 112, 113, 114, 115])],
    },
    {
        'name': "Administrer Odoo 19 CE", 'blog': BLOG_FONC, 'version': '19.0',
        'audience': "Intermédiaire · administrateur", 'tag': 'serie-fonc-s12-administration',
        'description': "Multi-société, droits d'accès, plans comptables, rapports et paramétrage, "
                       "jusqu'à la checklist de mise en service.",
        'blocks': [(None, [122, 124, 126, 131, 134, 136, 137])],
    },
    {
        'name': "Restaurant", 'blog': BLOG_FONC, 'version': '19.0',
        'audience': "Débutant · restaurateur", 'tag': None,
        'description': "Configuration, plan de salle, commande envoyée en cuisine, addition, "
                       "carte et libre-service par QR.",
        'blocks': [(None, [154, 155, 156, 157, 158, 159])],
    },
    {
        'name': "Reprendre ses données", 'blog': BLOG_FONC, 'version': '19.0',
        'audience': "Intermédiaire · consultant et chef de projet", 'tag': 'serie-fonc-s13-reprise-donnees',
        'description': "Clients et fournisseurs, catalogue, stock initial et balance d'ouverture : "
                       "importer l'existant, puis le recetter.",
        'blocks': [(None, [172, 173, 174, 175, 176])],
    },
    {
        'name': "Traduire Odoo (fonctionnel)", 'blog': BLOG_FONC, 'version': '19.0',
        'audience': "Débutant · utilisateur métier", 'tag': None,
        'description': "Traduire Odoo sans écrire de code, puis publier un site multilingue "
                       "avec l'arabe et l'écriture de droite à gauche.",
        'blocks': [(None, [167, 168])],
    },
]

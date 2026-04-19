"""Fixtures partagées pour les tests du module odooskills_helpdesk.

Ce module fournit la classe HelpdeskCommon qui instancie les objets
de test réutilisables (catégories, tags, partner, ticket de base).
"""
from odoo.tests import TransactionCase, new_test_user


class HelpdeskCommon(TransactionCase):
    """Classe de base pour tous les tests helpdesk.

    setUpClass crée des fixtures persistantes pour la durée de la suite.
    Chaque méthode de test tourne dans sa propre transaction annulée
    (comportement standard TransactionCase).
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Utilisateur interne dédié aux tests helpdesk
        cls.user_helpdesk = new_test_user(
            cls.env,
            login='user_helpdesk_test',
            groups='base.group_user',
        )

        # Partenaire client standard
        cls.partner_customer = cls.env['res.partner'].create({
            'name': 'Client Test',
            'email': 'client.test@example.com',
        })

        # Catégorie racine pour les tests de base
        # Note : category_child est créé dans setUp() des tests qui l'utilisent
        # pour éviter les conflits de contrainte UNIQUE entre les passes de test
        cls.category_root = cls.env['helpdesk.ticket.category'].create({
            'name': 'Technique',
        })

        # Tag pour filtrage et association Many2many
        cls.tag_urgent = cls.env['helpdesk.ticket.tag'].create({
            'name': 'Urgent',
            'color': 1,
        })

        # Ticket de base réutilisable (lecture seule dans les tests)
        cls.ticket_template = cls.env['helpdesk.ticket'].with_context(
            skip_mail=True
        ).create({
            'name': 'Ticket de test commun',
            'partner_id': cls.partner_customer.id,
            'category_id': cls.category_root.id,
        })

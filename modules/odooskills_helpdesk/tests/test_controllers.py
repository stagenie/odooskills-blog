"""Tests des controllers HTTP du module odooskills_helpdesk.

Couvre :
- Page publique /helpdesk/status/<ref> : status 200, contenu, ticket inconnu
- API JSON /api/v1/tickets : création authentifiée, liste, lecture par référence

Note : HttpCase ne peut pas hériter de HelpdeskCommon (conflits de transactions).
Les fixtures sont créées dans setUp avec un user de test dédié.
"""
import json

from odoo.tests import HttpCase, tagged, new_test_user


@tagged('post_install', '-at_install')
class TestControllers(HttpCase):
    """Tests des controllers HTTP de odooskills_helpdesk."""

    def setUp(self):
        super().setUp()
        # Créer un utilisateur interne avec password connu pour authenticate()
        self.test_user = new_test_user(
            self.env,
            login='ctrl_test_user',
            password='ctrl_test_pass_123',
            groups='base.group_user,base.group_system',
        )
        self.partner = self.env['res.partner'].create({
            'name': 'Client Controller Test',
            'email': 'ctrl.test@example.com',
        })
        self.ticket = self.env['helpdesk.ticket'].with_context(skip_mail=True).create({
            'name': 'Ticket Controller Test',
            'partner_id': self.partner.id,
        })
        self.env.flush_all()
        self.ticket_ref = self.ticket.reference
        self.ticket_id = self.ticket.id
        self.partner_id = self.partner.id

    def _db_header(self):
        """Retourne l'en-tête X-Odoo-Database nécessaire aux requêtes HTTP sans session."""
        return {'X-Odoo-Database': self.env.cr.dbname}

    # ── 1. Page publique — ticket existant ────────────────────────────────

    def test_ticket_page_public_status_200(self):
        """GET /helpdesk/status/<ref> avec une référence valide -> HTTP 200."""
        response = self.url_open(
            f'/helpdesk/status/{self.ticket_ref}',
            headers=self._db_header(),
        )
        self.assertEqual(response.status_code, 200,
                         "La page publique doit retourner HTTP 200 pour un ticket valide.")

    def test_ticket_page_contains_reference(self):
        """Le body de la page publique doit contenir la référence du ticket."""
        response = self.url_open(
            f'/helpdesk/status/{self.ticket_ref}',
            headers=self._db_header(),
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            self.ticket_ref.encode(),
            response.content,
            "La référence du ticket doit apparaître dans la page publique.",
        )

    # ── 2. Page publique — ticket inconnu ─────────────────────────────────

    def test_ticket_page_not_found_message(self):
        """GET /helpdesk/status/BIDON -> HTTP 200 avec message 'introuvable'."""
        response = self.url_open(
            '/helpdesk/status/HLP-9999-BIDON',
            headers=self._db_header(),
        )
        self.assertEqual(response.status_code, 200,
                         "La page doit retourner 200 même pour un ticket inexistant.")
        self.assertIn(b'introuvable', response.content,
                      "La page doit afficher 'introuvable' pour une référence inconnue.")

    # ── 3. Page publique — ticket résolu ──────────────────────────────────

    def test_ticket_page_resolved_shows_badge(self):
        """Un ticket en état 'done' -> la page doit afficher le badge 'Résolu'."""
        self.ticket.with_context(skip_mail=True).write({'state': 'done'})
        self.env.flush_all()

        response = self.url_open(
            f'/helpdesk/status/{self.ticket_ref}',
            headers=self._db_header(),
        )
        self.assertEqual(response.status_code, 200)
        # Le template affiche le badge "Résolu" (text-bg-success) quand state == 'done'
        self.assertIn(b'solu', response.content,
                      "La page doit contenir 'Résolu' quand le ticket est done.")

    # ── 4. API JSON — création authentifiée ──────────────────────────────

    def test_json_create_ticket_authenticated(self):
        """POST /api/v1/tickets avec action=create -> retourne id et reference."""
        self.authenticate('ctrl_test_user', 'ctrl_test_pass_123')

        payload = {
            'jsonrpc': '2.0',
            'method': 'call',
            'params': {
                'action': 'create',
                'name': 'Ticket via API JSON test',
                'partner_id': self.partner_id,
                'channel': 'email',
            },
        }
        response = self.url_open(
            '/api/v1/tickets',
            data=json.dumps(payload),
            headers={'Content-Type': 'application/json'},
        )
        self.assertEqual(response.status_code, 200)

        result = response.json().get('result', {})
        self.assertIn('id', result,
                      "La réponse JSON doit contenir un champ 'id'.")
        self.assertIn('reference', result,
                      "La réponse JSON doit contenir un champ 'reference'.")
        self.assertGreater(result['id'], 0,
                           "L'id retourné doit être un entier positif.")

    # ── 5. API JSON — liste authentifiée ─────────────────────────────────

    def test_json_list_tickets_authenticated(self):
        """POST /api/v1/tickets avec action=list -> retourne count et tickets."""
        self.authenticate('ctrl_test_user', 'ctrl_test_pass_123')

        payload = {
            'jsonrpc': '2.0',
            'method': 'call',
            'params': {
                'action': 'list',
                'limit': 5,
            },
        }
        response = self.url_open(
            '/api/v1/tickets',
            data=json.dumps(payload),
            headers={'Content-Type': 'application/json'},
        )
        self.assertEqual(response.status_code, 200)

        result = response.json().get('result', {})
        self.assertIn('count', result,
                      "La réponse JSON doit contenir un champ 'count'.")
        self.assertIn('tickets', result,
                      "La réponse JSON doit contenir un champ 'tickets'.")

    # ── 6. API JSON — action inconnue retourne erreur ─────────────────────

    def test_json_unknown_action_returns_error(self):
        """POST /api/v1/tickets avec action=unknown -> retourne {'error': ...}."""
        self.authenticate('ctrl_test_user', 'ctrl_test_pass_123')

        payload = {
            'jsonrpc': '2.0',
            'method': 'call',
            'params': {
                'action': 'this_action_does_not_exist',
            },
        }
        response = self.url_open(
            '/api/v1/tickets',
            data=json.dumps(payload),
            headers={'Content-Type': 'application/json'},
        )
        self.assertEqual(response.status_code, 200)

        result = response.json().get('result', {})
        self.assertIn('error', result,
                      "Une action inconnue doit retourner un champ 'error' dans la réponse.")

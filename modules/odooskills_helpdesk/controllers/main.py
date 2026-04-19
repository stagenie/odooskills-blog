"""Controllers HTTP pour le module odooskills_helpdesk.

Trois routes pédagogiques :

1. /api/v1/tickets       (JSON, auth=user)  -> lister / créer des tickets
2. /api/v1/tickets/<ref> (JSON, auth=user)  -> lire un ticket par référence
3. /helpdesk/status/<ref> (HTTP public, QWeb) -> page de suivi client
"""
from odoo import http
from odoo.http import request


class HelpdeskController(http.Controller):

    # ──────────────────────────────────────────────────────────────────────
    # 1. API REST JSON — auth=user (session Odoo obligatoire)
    # ──────────────────────────────────────────────────────────────────────

    @http.route('/api/v1/tickets', type='json', auth='user', methods=['POST'])
    def api_tickets(self, **kwargs):
        """Lister ou créer un ticket.

        Payload JSON :
          - action='list'  -> renvoie la liste des tickets accessibles
          - action='create' -> crée un ticket, requiert name + partner_id
        """
        action = kwargs.get('action', 'list')
        Ticket = request.env['helpdesk.ticket']

        if action == 'list':
            domain = kwargs.get('domain') or []
            limit = min(int(kwargs.get('limit', 20)), 100)
            tickets = Ticket.search(domain, limit=limit, order='create_date desc')
            return {
                'count': len(tickets),
                'tickets': [{
                    'id': t.id,
                    'reference': t.reference,
                    'name': t.name,
                    'state': t.state,
                    'priority': t.priority,
                    'partner': t.partner_id.name,
                    'create_date': t.create_date.isoformat() if t.create_date else None,
                } for t in tickets],
            }

        if action == 'create':
            required = {'name', 'partner_id'}
            if not required.issubset(kwargs):
                return {'error': f"missing fields: {required - kwargs.keys()}"}
            ticket = Ticket.create({
                'name': kwargs['name'],
                'partner_id': int(kwargs['partner_id']),
                'category_id': int(kwargs.get('category_id') or 0) or False,
                'channel': kwargs.get('channel', 'email'),
                'description': kwargs.get('description', ''),
            })
            return {
                'id': ticket.id,
                'reference': ticket.reference,
                'state': ticket.state,
            }

        return {'error': f"unknown action '{action}'"}

    @http.route('/api/v1/tickets/<string:ref>', type='json', auth='user', methods=['POST'])
    def api_ticket_read(self, ref, **kwargs):
        """Lire un ticket par sa référence (ex: HLP/2026/00007)."""
        ticket = request.env['helpdesk.ticket'].search(
            [('reference', '=', ref)], limit=1,
        )
        if not ticket:
            return {'error': 'not found'}
        return {
            'id': ticket.id,
            'reference': ticket.reference,
            'name': ticket.name,
            'state': ticket.state,
            'priority': ticket.priority,
            'partner': {
                'id': ticket.partner_id.id,
                'name': ticket.partner_id.name,
                'email': ticket.partner_id.email,
            },
            'category': ticket.category_id.display_name,
            'assigned_to': ticket.user_id.name if ticket.user_id else None,
            'deadline': ticket.deadline.isoformat() if ticket.deadline else None,
            'description': ticket.description,
        }

    # ──────────────────────────────────────────────────────────────────────
    # 2. Route HTTP publique — page de suivi client
    # ──────────────────────────────────────────────────────────────────────

    @http.route('/helpdesk/status/<path:ref>', type='http', auth='public', website=True)
    def helpdesk_status_page(self, ref, **kwargs):
        """Page publique de tracking — rend le template odooskills_helpdesk.ticket_status.

        auth='public' = accessible sans session. On lit via sudo() pour bypasser
        les ACLs mais on NE RENVOIE QUE les champs sûrs (pas de description ni de
        notes internes).
        """
        ticket = request.env['helpdesk.ticket'].sudo().search(
            [('reference', '=', ref)], limit=1,
        )
        values = {'ref': ref, 'ticket': ticket}
        return request.render('odooskills_helpdesk.ticket_status_page', values)

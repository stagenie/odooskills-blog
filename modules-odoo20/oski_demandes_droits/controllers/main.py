from werkzeug.exceptions import NotFound

from odoo import http
from odoo.http import request

CHAMPS = ['name', 'user_id', 'company_id', 'montant', 'state']


class DemandesController(http.Controller):

    @http.route('/oski/demandes/<int:demande_id>/json', type='http', auth='user', methods=['GET'])
    def demande_json(self, demande_id):
        # Pas de sudo() : browse() dans l'environnement de l'utilisateur connecté,
        # puis has_access() avant de lire. Une demande d'un autre = 404, comme une demande absente.
        demande = request.env['oski.demande'].browse(demande_id).exists()
        if not demande or not demande.has_access('read'):
            raise NotFound()
        return request.make_json_response(demande.read(CHAMPS, load=None)[0])

    @http.route('/oski/demandes/stats', type='http', auth='public', methods=['GET'])
    def demandes_stats(self):
        # sudo() utile et borné : des comptages, aucun enregistrement ne sort.
        return request.make_json_response(request.env['oski.demande']._stats_publiques())

    @http.route('/oski/api/demandes', type='http', auth='bearer', bearer_scope='rpc', methods=['GET'], csrf=False)
    def api_demandes(self):
        # Clé d'API : la requête s'exécute sous l'utilisateur de la clé, avec ses droits.
        demandes = request.env['oski.demande'].search([])
        return request.make_json_response(demandes.read(CHAMPS, load=None))

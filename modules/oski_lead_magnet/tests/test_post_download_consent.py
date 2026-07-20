"""Écran de confirmation : consentement donné APRÈS le téléchargement.

L'accord n'est plus demandé pendant que l'internaute vise le bouton de
téléchargement, mais une fois le PDF obtenu. Le clic est un acte positif
explicite, donc un consentement valide — jamais une case pré-cochée.
"""
import json

from odoo.tests import HttpCase, TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestGrantConsentModel(TransactionCase):
    def setUp(self):
        super().setUp()
        self.Capture = self.env['oski.lead.capture']

    def _liste(self):
        return self.Capture._prospects_list()

    def test_grant_consent_inscrit_a_la_liste(self):
        self.Capture._oski_grant_consent('tardif@example.com')
        contact = self.env['mailing.contact'].search(
            [('email', '=ilike', 'tardif@example.com')], limit=1)
        self.assertTrue(contact, "le contact doit être créé")
        self.assertIn(self._liste(), contact.list_ids)

    def test_grant_consent_idempotent(self):
        self.Capture._oski_grant_consent('deuxfois@example.com')
        self.Capture._oski_grant_consent('deuxfois@example.com')
        contacts = self.env['mailing.contact'].search(
            [('email', '=ilike', 'deuxfois@example.com')])
        self.assertEqual(len(contacts), 1, "pas de doublon de contact")
        self.assertEqual(len(contacts.list_ids), 1, "pas d'inscription en double")

    def test_grant_consent_email_invalide_refuse(self):
        self.assertFalse(self.Capture._oski_grant_consent('pas-un-email'))
        self.assertFalse(self.Capture._oski_grant_consent(''))

    def test_is_subscribed_reflete_l_etat(self):
        self.assertFalse(self.Capture._oski_is_subscribed('inconnu@example.com'))
        self.Capture._oski_grant_consent('inconnu@example.com')
        self.assertTrue(self.Capture._oski_is_subscribed('inconnu@example.com'))

    def test_capture_sans_consentement_n_inscrit_pas(self):
        """Le cœur du dispositif : sans case cochée, pas d'inscription."""
        self.Capture._oski_capture_lead('sansaccord@example.com', False, 'pdf')
        self.assertFalse(self.Capture._oski_is_subscribed('sansaccord@example.com'))

    def test_capture_expose_l_etat_d_inscription(self):
        res = self.Capture._oski_capture_lead('flag@example.com', False, 'pdf')
        self.assertFalse(res['subscribed'], "doit dire non inscrit")
        res = self.Capture._oski_capture_lead('flag@example.com', True, 'pdf')
        self.assertTrue(res['subscribed'], "doit dire inscrit après accord")


@tagged('post_install', '-at_install')
class TestGrantConsentHttp(HttpCase):
    def _post(self, route, params=None):
        return self.url_open(
            route,
            data=json.dumps({'jsonrpc': '2.0', 'method': 'call',
                             'params': params or {}}),
            headers={'Content-Type': 'application/json'},
        )

    def test_consent_sans_session_refuse(self):
        """Garde-fou : la route ne doit rien inscrire sans capture préalable."""
        res = self._post('/oski/lead/consent').json()['result']
        self.assertFalse(res['ok'])
        self.assertEqual(res['error'], 'no_session')

    def test_consent_utilise_l_email_de_la_session(self):
        session = self.opener  # conserve les cookies entre les deux appels
        self.assertTrue(session)
        self._post('/oski/lead/subscribe',
                   {'email': 'session@example.com', 'consent': False, 'source': 'pdf'})
        res = self._post('/oski/lead/consent').json()['result']
        self.assertTrue(res['ok'])
        self.assertTrue(
            self.env['oski.lead.capture']._oski_is_subscribed('session@example.com'))

    def test_consent_n_accepte_aucun_email_en_parametre(self):
        """Sécurité : impossible d'inscrire l'adresse d'un tiers.

        La route ignore tout paramètre et n'utilise que la session, sinon
        n'importe qui pourrait abonner n'importe quelle adresse.
        """
        self._post('/oski/lead/subscribe',
                   {'email': 'moi@example.com', 'consent': False, 'source': 'pdf'})
        self._post('/oski/lead/consent', {'email': 'victime@example.com'})
        self.assertFalse(
            self.env['oski.lead.capture']._oski_is_subscribed('victime@example.com'),
            "l'adresse d'un tiers ne doit jamais être inscrite")
        self.assertTrue(
            self.env['oski.lead.capture']._oski_is_subscribed('moi@example.com'))

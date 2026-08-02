import json

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestOskiPromoDetector(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.website = cls.env['website'].search([], limit=1)

    def _page(self, arch, url):
        vue = self.env['ir.ui.view'].create({
            'name': 'TEST DETECT %s' % url, 'type': 'qweb',
            'key': 'oski_promo.test_detect_%s' % url.strip('/'),
            'arch': arch,
        })
        return self.env['website.page'].create({
            'view_id': vue.id, 'url': url, 'website_published': True,
        })

    def test_detecte_prix_dans_la_prose(self):
        self._page('<t name="P"><div><p>Accès complet à 24 €.</p></div></t>',
                   '/test-prose')
        trouve = self.website.oski_scan_hardcoded_prices()
        self.assertTrue(any(f['url'] == '/test-prose' for f in trouve))

    def test_ignore_le_bloc_tarif(self):
        self._page(
            '<t name="P"><div><span data-oski-price="EBOOK-E1">'
            '<span>27 €</span><span>24 €</span></span></div></t>',
            '/test-bloc')
        trouve = self.website.oski_scan_hardcoded_prices()
        self.assertFalse(any(f['url'] == '/test-bloc' for f in trouve))

    def test_page_sans_prix_non_signalee(self):
        self._page('<t name="P"><div><p>Formation Odoo 19 complète.</p></div></t>',
                   '/test-propre')
        trouve = self.website.oski_scan_hardcoded_prices()
        self.assertFalse(any(f['url'] == '/test-propre' for f in trouve))

    def test_rapporte_la_valeur_et_un_extrait(self):
        self._page('<t name="P"><div><p>Économisez 11 € sur le pack.</p></div></t>',
                   '/test-extrait')
        trouve = [f for f in self.website.oski_scan_hardcoded_prices()
                  if f['url'] == '/test-extrait']
        self.assertEqual(len(trouve), 1)
        self.assertIn('11', trouve[0]['value'])
        self.assertIn('Économisez', trouve[0]['excerpt'])

    def test_detecte_prix_juste_apres_un_bloc_tarif(self):
        # Le texte qui suit un bloc tarif (.tail en lxml) ne doit pas
        # disparaître avec lui quand le nœud est retiré de l'arbre.
        self._page(
            '<t name="P"><div><p>Prix normal :'
            '<span data-oski-price="EBOOK-E1">'
            '<span>27 €</span><span>24 €</span></span>'
            ' Offre valable jusqu\'au 15 août à 19 € !</p></div></t>',
            '/test-tail')
        trouve = [f for f in self.website.oski_scan_hardcoded_prices()
                  if f['url'] == '/test-tail']
        self.assertTrue(any(f['value'] == '19' for f in trouve))

    def test_detecte_prix_dans_un_attribut(self):
        # Un prix porté par un attribut (ex. data-price-regular sur les
        # anciennes landing pages) est invisible au rendu textuel mais
        # réécrit le DOM au même titre qu'un prix en clair — souvent
        # réécrit en JS toutes les secondes. Le canal attribut doit être
        # scanné au même titre que le texte.
        self._page(
            '<t name="P"><div><span class="lp-ebook-price" '
            'data-price-launch="16,80 €" data-price-regular="24 €">'
            '16,80 €</span></div></t>',
            '/test-attribut')
        trouve = [f for f in self.website.oski_scan_hardcoded_prices()
                  if f['url'] == '/test-attribut']
        self.assertTrue(any(f['channel'] == 'attribut' and f['value'] == '24'
                             for f in trouve))
        self.assertTrue(any(f['channel'] == 'attribut' and f['value'] == '16,80'
                             for f in trouve))

    def test_ignore_les_attributs_du_bloc_tarif(self):
        # data-after / data-barre / data-after-value / data-oski-price
        # sont recalculés à chaque rendu par oski_price() : ce ne sont pas
        # des prix en dur, même logique d'exclusion que pour le texte du
        # bloc.
        self._page(
            '<t name="P"><div><span data-oski-price="EBOOK-E1" '
            'data-after="16,80" data-barre="27.0" data-after-value="16.8">'
            '<span>27 €</span><span>16,80 €</span></span></div></t>',
            '/test-bloc-attribut')
        trouve = [f for f in self.website.oski_scan_hardcoded_prices()
                  if f['url'] == '/test-bloc-attribut']
        self.assertFalse(any(f['channel'] == 'attribut' for f in trouve))

    def test_detecte_montant_ecrit_en_toutes_lettres(self):
        # Le détecteur de PRODUCTION doit voir « 24 euros » aussi bien que
        # « 24 € » : sinon une page qui vante « la formation à 24 euros »
        # rend une liste vide et délivre un quitus mensonger.
        self._page('<t name="P"><div><p>La formation à 24 euros.</p></div></t>',
                   '/test-euros')
        trouve = [f for f in self.website.oski_scan_hardcoded_prices()
                  if f['url'] == '/test-euros']
        self.assertTrue(any(f['value'] == '24' for f in trouve))

    def test_lit_les_milliers_en_entier(self):
        # « 1 500 € » doit être lu comme 1 500, jamais comme 500 : un
        # signalement à 500 envoie corriger un montant qui n'existe pas.
        self._page('<t name="P"><div><p>Prestation sur mesure à 1 500 €.</p>'
                   '</div></t>', '/test-milliers')
        trouve = [f for f in self.website.oski_scan_hardcoded_prices()
                  if f['url'] == '/test-milliers']
        valeurs = {f['value'] for f in trouve}
        self.assertIn('1 500', valeurs)
        self.assertNotIn('500', valeurs)

    def test_faux_amis_non_signales(self):
        # « meilleur », « heure(s) », « leur », « européens » contiennent
        # tous la séquence « eur ». Aucun ne doit être signalé, sinon le
        # détecteur devient du bruit qu'on finit par ignorer.
        self._page(
            '<t name="P"><div><p>Le meilleur atelier de 14 heures pour les '
            'européens : leur montée en compétence en 3 heures par module, '
            "et 12 leurres de moins qu'ailleurs.</p></div></t>",
            '/test-faux-amis')
        trouve = [f for f in self.website.oski_scan_hardcoded_prices()
                  if f['url'] == '/test-faux-amis']
        self.assertEqual(trouve, [])

    def test_page_cassee_n_empeche_pas_le_scan_des_autres(self):
        # Une page à l'arch non parsable ne doit pas interrompre le scan
        # des pages suivantes. ir.ui.view valide l'XML à l'écriture, donc
        # on corrompt arch_db directement en base pour simuler un arch
        # réellement illisible (cas d'une déclaration XML mal supportée
        # par lxml.etree.fromstring sur une chaîne unicode, entre autres).
        page_cassee = self._page(
            '<t name="P"><div><p>Provisoire</p></div></t>', '/test-cassee')
        self.env.cr.execute(
            "UPDATE ir_ui_view SET arch_db = %s WHERE id = %s",
            (json.dumps({'en_US': '<?xml version="1.0" encoding="utf-8"?>'
                                   '<t name="P"><p>Incomplet'}),
             page_cassee.view_id.id))
        page_cassee.view_id.invalidate_recordset(['arch_db', 'arch'])

        self._page('<t name="P"><div><p>Accès complet à 24 €.</p></div></t>',
                   '/test-apres-cassee')
        trouve = self.website.oski_scan_hardcoded_prices()
        self.assertTrue(any(f['url'] == '/test-apres-cassee' for f in trouve))

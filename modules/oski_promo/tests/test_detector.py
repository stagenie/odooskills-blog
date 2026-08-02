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

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestSlaBadgeRegistration(TransactionCase):
    """Teste que le widget sla_badge est bien enregistré côté serveur via l'asset bundle."""

    def test_manifest_declares_assets(self):
        """Le manifest doit charger les 3 fichiers statiques du widget dans web.assets_backend."""
        module = self.env['ir.module.module'].search([('name', '=', 'odooskills_helpdesk')], limit=1)
        self.assertTrue(module, "Module odooskills_helpdesk introuvable")
        # Lecture du manifest via get_manifest
        from odoo.modules.module import get_manifest
        manifest = get_manifest('odooskills_helpdesk')
        assets = manifest.get('assets', {})
        backend = assets.get('web.assets_backend', [])
        paths = [p if isinstance(p, str) else p[1] for p in backend]
        self.assertTrue(
            any('sla_badge.js' in p for p in paths),
            f"sla_badge.js absent de web.assets_backend (trouvé : {paths})",
        )
        self.assertTrue(
            any('sla_badge.xml' in p for p in paths),
            f"sla_badge.xml absent de web.assets_backend (trouvé : {paths})",
        )
        self.assertTrue(
            any('sla_badge.scss' in p for p in paths),
            f"sla_badge.scss absent de web.assets_backend (trouvé : {paths})",
        )

    def test_inherit_view_loads(self):
        """La vue inherit doit exister et cibler bien la form ticket."""
        view = self.env.ref('odooskills_helpdesk.view_helpdesk_ticket_form_t26_sla_badge')
        self.assertEqual(view.model, 'helpdesk.ticket')
        self.assertEqual(view.inherit_id.xml_id, 'odooskills_helpdesk.view_helpdesk_ticket_form')
        # L'arch doit référencer widget="sla_badge"
        self.assertIn('sla_badge', view.arch)

    def test_existing_sla_computation_still_works(self):
        """Régression : le champ sla_status continue d'être calculé correctement."""
        partner = self.env['res.partner'].create({'name': 'Widget Test Client'})
        ticket = self.env['helpdesk.ticket'].create({
            'name': 'Test SLA widget',
            'partner_id': partner.id,
            'sla_hours': 48,
        })
        self.assertIn(ticket.sla_status, ('ok', 'warning', 'breach'),
                      "sla_status doit toujours être calculé via mixin")

"""T28 — Tests du helper bench _bench_bulk_escalate.

Valide que la méthode retourne la forme attendue et des timings cohérents,
avec et sans push bus.bus. N = 5 pour rester rapide en CI.
"""
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install', 'odooskills_t28')
class TestBenchHelper(TransactionCase):
    """T28 — helper bench : validation forme et cohérence timings."""

    def setUp(self):
        super().setUp()
        # 10 tickets suffisent pour valider la logique — on n'a pas besoin de 10k en CI
        self.env['helpdesk.ticket'].with_context(skip_mail=True).create([
            {'name': f'Bench-{i}', 'sla_hours': 48} for i in range(10)
        ])

    def test_bench_returns_shape_with_push(self):
        """La méthode doit retourner les 4 clés attendues avec push=True."""
        result = self.env['helpdesk.ticket']._bench_bulk_escalate(n=5, push=True)

        self.assertIn('n', result)
        self.assertIn('total_ms', result)
        self.assertIn('per_ticket_ms', result)
        self.assertIn('push', result)

        self.assertEqual(result['n'], 5)
        self.assertGreater(result['total_ms'], 0)
        self.assertGreater(result['per_ticket_ms'], 0)
        self.assertTrue(result['push'])

    def test_bench_no_push_shape(self):
        """La méthode doit retourner push=False quand le paramètre est False."""
        result = self.env['helpdesk.ticket']._bench_bulk_escalate(n=5, push=False)

        self.assertEqual(result['n'], 5)
        self.assertGreater(result['total_ms'], 0)
        self.assertGreater(result['per_ticket_ms'], 0)
        self.assertFalse(result['push'])

    def test_bench_result_n_matches_limit(self):
        """Le champ 'n' doit correspondre au nombre réel de tickets traités."""
        # On demande 3 tickets — setUp en a créé 10, donc on doit en avoir 3
        result = self.env['helpdesk.ticket']._bench_bulk_escalate(n=3, push=True)
        self.assertEqual(result['n'], 3)
        self.assertGreater(result['total_ms'], 0)
        self.assertTrue(result['push'])

    def test_per_ticket_ms_coherent(self):
        """per_ticket_ms doit être cohérent avec total_ms / n (à 1 ms près)."""
        result = self.env['helpdesk.ticket']._bench_bulk_escalate(n=5, push=False)
        expected = round(result['total_ms'] / result['n'], 4)
        # On tolère un écart de 0.01 ms (arrondi de round())
        self.assertAlmostEqual(result['per_ticket_ms'], expected, delta=0.01)

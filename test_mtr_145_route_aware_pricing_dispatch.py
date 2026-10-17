import unittest
from types import SimpleNamespace
from qseries_v2.oracle_execution.solana_atomic_executor.mtr_144_route_identity_latest_queue import RouteKey, Queued, SIZES
from qseries_v2.oracle_execution.solana_atomic_executor.mtr_145_route_aware_pricing_dispatch import RouteAwarePricer, DIRECTIONS

class Q:
    def __init__(self): self.rows = {}
    def take_if_current(self, key): return self.rows.get(key)

class Tests(unittest.TestCase):
    def setUp(self):
        self.q = Q()
        self.a = RouteKey("T", "P", "D1")
        self.b = RouteKey("T", "P", "D2")
        self.q.rows[self.a] = Queued(self.a, 1, 1, 10, 1000, "snapshot1")
        self.q.rows[self.b] = Queued(self.b, 1, 1, 10, 1000, "snapshot2")

    def test_independent_same_token_routes(self):
        p = RouteAwarePricer(self.q, lambda s, d, z: (1 if s == "snapshot1" else -1, 1.0 if s == "snapshot1" else -1.0))
        x, y = p.sweep(self.a, 1100), p.sweep(self.b, 1100)
        self.assertEqual(len(x), 10)
        self.assertEqual(len(y), 10)
        self.assertTrue(all(t.net_raw == 1 for t in x))
        self.assertTrue(all(t.net_raw == -1 for t in y))

    def test_full_bidirectional_sizes(self):
        p = RouteAwarePricer(self.q, lambda s, d, z: (0, 0.0))
        rows = p.sweep(self.a, 1100)
        self.assertEqual({x.direction for x in rows}, set(DIRECTIONS))
        self.assertEqual({x.size for x in rows}, set(SIZES))
        self.assertEqual(len(rows), 10)

    def test_mid_sweep_replacement_aborts(self):
        def pricing(s, d, z):
            self.q.rows[self.a] = Queued(self.a, 1, 2, 11, 1010, "new")
            return 4, 1.0
        p = RouteAwarePricer(self.q, pricing)
        self.assertEqual(p.sweep(self.a, 1100), ())
        self.assertEqual(p.stats["aborted"], 1)

    def test_stale_rejected_before_pricing(self):
        def fail(*args): raise AssertionError("should not price")
        self.assertEqual(RouteAwarePricer(self.q, fail, 99).sweep(self.a, 1100), ())

    def test_unknown_route_rejected(self):
        self.assertEqual(RouteAwarePricer(self.q, lambda *a: (0, 0.0)).sweep(RouteKey("X", "P", "D"), 1100), ())

    def test_invalid_economics_rejected(self):
        with self.assertRaises(ValueError):
            RouteAwarePricer(self.q, lambda *a: (0, float("nan"))).sweep(self.a, 1100)

    def test_candidate_filter_not_execution_authority(self):
        p = RouteAwarePricer(self.q, lambda *a: (100, 2.0))
        rows = p.sweep(self.a, 1100)
        self.assertEqual(len(p.candidates(rows)), 10)
        self.assertFalse(hasattr(p, "send_transaction"))

if __name__ == "__main__":
    unittest.main(verbosity=2)

import inspect
import unittest

from qseries_v2.oracle_execution import oracle_028_exact_immutable_atomic_shadow_handoff as q28

class T(unittest.TestCase):
    def test_safety(self):
        self.assertFalse(q28.EXECUTION_AUTHORITY)
        self.assertTrue(q28.PAPER_ONLY)
        self.assertFalse(q28.REAL_MONEY_MOVED)

    def test_current_scan_handoff(self):
        src = inspect.getsource(q28.ShadowLane._price)
        self.assertIn("best = max(rows", src)
        self.assertIn("self.shadow.submit(best)", src)
        self.assertNotIn("best=self.best", src)

    def test_exact_size_preserved(self):
        src = inspect.getsource(q28.AtomicShadow._loop)
        self.assertIn('size = float(best["size_sol"])', src)
        self.assertIn("compose_reverse_candidates", src)

    def test_latest_only_and_backoff(self):
        self.assertIn("self.latest[token] = dict(best)", inspect.getsource(q28.AtomicShadow.submit))
        self.assertIn("_mark_429", inspect.getsource(q28.AtomicShadow._loop))

    def test_no_broadcast(self):
        self.assertNotIn("sendTransaction", inspect.getsource(q28))

if __name__ == "__main__":
    unittest.main(verbosity=2)

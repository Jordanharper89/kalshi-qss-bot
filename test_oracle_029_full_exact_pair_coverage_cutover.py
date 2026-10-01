import inspect
import unittest

from qseries_v2.oracle_execution import oracle_029_full_exact_pair_coverage_cutover as q29

class T(unittest.TestCase):
    def test_safety(self):
        self.assertFalse(q29.EXECUTION_AUTHORITY)
        self.assertTrue(q29.PAPER_ONLY)
        self.assertFalse(q29.REAL_MONEY_MOVED)

    def test_coverage_target(self):
        self.assertEqual(q29.TARGET_EXACT_PAIRS, 12)

    def test_lifts_exact_hydrator_before_prepare(self):
        src = inspect.getsource(q29.expanded_prepare_once)
        self.assertIn("q60b.install()", src)
        self.assertIn("q60b.m.pd.MAX_PAIRS", src)
        self.assertIn("q60b.extended_prepare(root)", src)

    def test_preserves_oracle_028(self):
        src = inspect.getsource(q29.run)
        self.assertIn("q28.run(float(seconds))", src)

    def test_no_broadcast(self):
        src = inspect.getsource(q29)
        self.assertNotIn("sendTransaction", src)

if __name__ == "__main__":
    unittest.main(verbosity=2)

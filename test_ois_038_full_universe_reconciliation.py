import unittest
from qseries_v2.oracle_intelligence_state.ois_038_universe_reconciliation import *

class T(unittest.TestCase):
    def test_verifier(self):
        self.assertTrue(verify_ois_038_full_universe_reconciliation())

    def test_added_removed(self):
        r=reconcile_market_universe(("A",),("B",))
        self.assertEqual(r.added,("B",))
        self.assertEqual(r.removed,("A",))

    def test_empty_discovered(self):
        with self.assertRaises(ValueError):
            reconcile_market_universe(("A",),())

if __name__=="__main__":
    print("="*72);print(" OIS-038 CERTIFICATION TEST");print(" FULL-UNIVERSE RECONCILIATION");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Deterministic full-universe adapter reconciliation certified")
    print("[DONE] OIS-038 CERTIFIED")

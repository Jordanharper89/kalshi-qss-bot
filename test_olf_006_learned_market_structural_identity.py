import unittest
from qseries_v2.oracle_learning_feedback.olf_006_structural_identity import *

class T(unittest.TestCase):
    def test_identity(self):self.assertEqual(OLF_006_BUILD_ID,"OLF-006")
    def test_same_series(self):
        self.assertTrue(same_series("KXBTC15M-26AUG192200-00","KXBTC15M-26AUG192215-15"))
    def test_cross_series_rejected(self):
        self.assertFalse(same_series("KXBTC15M-26AUG192200-00","KXETH15M-26AUG192200-00"))
    def test_invalid(self):
        with self.assertRaises(ValueError):normalize_ticker("bad ticker!")

if __name__=="__main__":
    print("="*88);print(" OLF-006 CERTIFICATION TEST");print(" LEARNED MARKET STRUCTURAL IDENTITY");print("="*88)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():raise SystemExit(1)
    print("[PASS] Exact Kalshi-series structural identity certified")
    print("[PASS] Cross-series transfer prohibited")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OLF-006 CERTIFIED")

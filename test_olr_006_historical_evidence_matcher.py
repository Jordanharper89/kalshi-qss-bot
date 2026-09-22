
import unittest
from qseries_v2.oracle_learning_runtime.olr_006_historical_evidence_matcher import *

class T(unittest.TestCase):
    def test_verifier(self):
        self.assertTrue(verify_olr_006_historical_evidence_matcher())

    def test_normalize(self):
        self.assertEqual(normalize_learning_ticker("kxtest-1"),"KXTEST-1")

    def test_bad(self):
        with self.assertRaises(ValueError):
            normalize_learning_ticker("x';drop")

if __name__=="__main__":
    print("="*72)
    print(" OLR-006 CERTIFICATION TEST")
    print(" HISTORICAL EVIDENCE MATCHER")
    print("="*72)
    result=unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not result.wasSuccessful():
        raise SystemExit(1)
    print("[PASS] Read-only historical market evidence matching certified")
    print("[DONE] OLR-006 CERTIFIED")

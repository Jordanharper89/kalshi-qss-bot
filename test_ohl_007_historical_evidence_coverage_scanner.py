
import unittest
from qseries_v2.oracle_historical_learning.ohl_007_historical_evidence_coverage_scanner import *

class T(unittest.TestCase):
    def test_verifier(self):self.assertTrue(verify_ohl_007_historical_evidence_coverage_scanner())
    def test_limit(self):
        with self.assertRaises(ValueError):scan_market_evidence_coverage(".","KX",0)

if __name__=="__main__":
    print("="*72);print(" OHL-007 CERTIFICATION TEST");print(" HISTORICAL EVIDENCE COVERAGE SCANNER");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():raise SystemExit(1)
    print("[PASS] Historical evidence coverage scanner certified")
    print("[DONE] OHL-007 CERTIFIED")

import unittest
from qseries_v2.oracle_pre_settlement_coverage.opc_002_bounded_open_market_sampler import *

class T(unittest.TestCase):
    def test_verifier(self):
        self.assertTrue(verify_opc_002_bounded_open_market_sampler())
    def test_bound(self):
        with self.assertRaises(ValueError):
            sample_live_open_markets(".",pages=11)

if __name__=="__main__":
    print("="*72)
    print(" OPC-002 CERTIFICATION TEST")
    print(" BOUNDED OPEN-MARKET SAMPLER")
    print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():
        raise SystemExit(1)
    print("[PASS] Bounded live-open market sampler certified")
    print("[DONE] OPC-002 CERTIFIED")

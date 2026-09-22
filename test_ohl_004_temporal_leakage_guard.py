import unittest
from qseries_v2.oracle_historical_learning.ohl_004_temporal_leakage_guard import *

class T(unittest.TestCase):
    def test_verifier(self):
        self.assertTrue(verify_ohl_004_temporal_leakage_guard())
    def test_empty_rejected(self):
        from qseries_v2.oracle_historical_learning.ohl_003_settled_market_evidence_reconstruction import SettledMarketTimeline
        g=guard_historical_timeline(SettledMarketTimeline("M","2026-01-02T00:00:00Z","YES",tuple(),0))
        self.assertFalse(g.admitted)

if __name__=="__main__":
    print("="*72)
    print(" OHL-004 CERTIFICATION TEST")
    print(" TEMPORAL LEAKAGE GUARD")
    print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Temporal Leakage Guard certified")
    print("[DONE] OHL-004 CERTIFIED")

import unittest
from qseries_v2.oracle_historical_learning.ohl_003_settled_market_evidence_reconstruction import *

class T(unittest.TestCase):
    def test_verifier(self):
        self.assertTrue(verify_ohl_003_settled_market_evidence_reconstruction())
    def test_post_settlement_excluded(self):
        x=reconstruct_settled_market_timeline("M","2026-01-02T00:00:00Z","YES",[
          {"observation_id":"x","market_id":"M","observed_at":"2026-01-02T00:00:00Z","payload":{}}])
        self.assertEqual(len(x.evidence),0)

if __name__=="__main__":
    print("="*72)
    print(" OHL-003 CERTIFICATION TEST")
    print(" SETTLED MARKET EVIDENCE RECONSTRUCTION")
    print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Settled Market Evidence Reconstruction certified")
    print("[DONE] OHL-003 CERTIFIED")

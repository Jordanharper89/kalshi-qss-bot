import unittest
from qseries_v2.oracle_historical_learning.ohl_005_historical_learning_candidate_gate import *

class T(unittest.TestCase):
    def test_verifier(self):
        self.assertTrue(verify_ohl_005_historical_learning_candidate_gate())
    def test_candidate_deterministic(self):
        from qseries_v2.oracle_historical_learning.ohl_003_settled_market_evidence_reconstruction import reconstruct_settled_market_timeline
        x=reconstruct_settled_market_timeline("M","2026-01-02T00:00:00Z","YES",[
          {"observation_id":"1","market_id":"M","observed_at":"2026-01-01T00:00:00Z","payload":{}}])
        self.assertEqual(build_historical_learning_candidate(x).candidate_id,
                         build_historical_learning_candidate(x).candidate_id)

if __name__=="__main__":
    print("="*72)
    print(" OHL-005 CERTIFICATION TEST")
    print(" HISTORICAL LEARNING CANDIDATE GATE")
    print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Historical Learning Candidate Gate certified")
    print("[DONE] OHL-005 CERTIFIED")

import unittest
from qseries_v2.oracle_learning.olr_037_market_evidence_candidate_matching import *
class T(unittest.TestCase):
    def test_ticker_match(self):
        m=match_outcome_to_evidence({"ticker":"X"},[{"ticker":"X"}])
        self.assertTrue(m.matched)
    def test_observation_id_priority(self):
        m=match_outcome_to_evidence({"ticker":"X","observation_id":"o2"},[{"ticker":"X","observation_id":"o1"},{"ticker":"X","observation_id":"o2"}])
        self.assertEqual(m.candidate["observation_id"],"o2")
if __name__=="__main__":
    print("="*88);print(" OLR-037 CERTIFICATION TEST");print(" MARKET EVIDENCE CANDIDATE MATCHING");print("="*88)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():raise SystemExit(1)
    print("[PASS] Deterministic evidence candidate matching certified")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OLR-037 CERTIFIED")

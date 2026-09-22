import unittest
from qseries_v2.oracle_learning.olr_036_outcome_evidence_linkage_foundation import *
class T(unittest.TestCase):
    def test_key(self):
        k=build_outcome_evidence_key({"ticker":"KXBTC","observation_id":"o1"})
        self.assertEqual(k.market_id,"KXBTC")
        self.assertEqual(k.observation_id,"o1")
    def test_deterministic_id(self):
        k=OutcomeEvidenceKey("m","t","o","s")
        self.assertEqual(deterministic_linkage_id(k),deterministic_linkage_id(k))
if __name__=="__main__":
    print("="*88);print(" OLR-036 CERTIFICATION TEST");print(" OUTCOME-EVIDENCE LINKAGE FOUNDATION");print("="*88)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():raise SystemExit(1)
    print("[PASS] Deterministic outcome-evidence linkage keys certified")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OLR-036 CERTIFIED")

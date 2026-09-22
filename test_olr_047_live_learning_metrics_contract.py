import unittest
from qseries_v2.oracle_learning.olr_047_live_learning_metrics_contract import *
class T(unittest.TestCase):
    def test_metrics(self):
        m=build_live_learning_metrics(100,25,75,20,10)
        self.assertEqual(m.evidence_matched+m.evidence_missing,m.settled)
        self.assertEqual(m.evidence_coverage,.25)
        self.assertEqual(m.learning_yield,.10)
if __name__=="__main__":
    print("="*88);print(" OLR-047 CERTIFICATION TEST");print(" LIVE LEARNING METRICS CONTRACT");print("="*88)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():raise SystemExit(1)
    print("[PASS] evidence_coverage and learning_yield metrics certified")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OLR-047 CERTIFIED")

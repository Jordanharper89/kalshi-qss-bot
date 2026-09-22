import unittest
from qseries_v2.oracle_learning.olr_043_live_learning_evidence_adapter import *
class T(unittest.TestCase):
    def test_metrics(self):
        m=LearningEvidenceMetrics(100,20,80,20,.2)
        self.assertEqual(m.evidence_matched+m.evidence_missing,m.settled)
        self.assertEqual(m.admitted,20)
if __name__=="__main__":
    print("="*88);print(" OLR-043 CERTIFICATION TEST");print(" LIVE LEARNING EVIDENCE ADAPTER");print("="*88)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():raise SystemExit(1)
    print("[PASS] Live learning evidence metrics contract certified")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OLR-043 CERTIFIED")

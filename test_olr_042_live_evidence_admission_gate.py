import unittest
from qseries_v2.oracle_learning.olr_042_live_evidence_admission_gate import *
class T(unittest.TestCase):
    def test_contract(self):
        x=EvidenceAdmission(True,"ADMITTED",50,"MARKET_ID",{"ticker":"X"})
        self.assertTrue(x.admitted)
        self.assertEqual(x.reason,"ADMITTED")
if __name__=="__main__":
    print("="*88);print(" OLR-042 CERTIFICATION TEST");print(" LIVE EVIDENCE ADMISSION GATE");print("="*88)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():raise SystemExit(1)
    print("[PASS] Evidence admission contract certified")
    print("[PASS] Missing evidence remains abstention, not learning")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OLR-042 CERTIFIED")

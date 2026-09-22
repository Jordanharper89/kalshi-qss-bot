import unittest
from qseries_v2.oracle_learning_runtime.olr_036_live_feedback_read_model import LiveCalibrationFeedback
from qseries_v2.oracle_learning_runtime.olr_037_learning_maturity_gate import *

class T(unittest.TestCase):
    def test_verifier(self):self.assertTrue(verify_olr_037_learning_maturity_gate())
    def test_low_sample_abstains(self):
        f=LiveCalibrationFeedback("KX",1,0,.2,.02,False,"insufficient_history",False,False)
        self.assertFalse(evaluate_learning_maturity(f).eligible)

if __name__=="__main__":
    print("="*72);print(" OLR-037 CERTIFICATION TEST");print(" LEARNING MATURITY GATE");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():raise SystemExit(1)
    print("[PASS] Learning maturity + reliability gating certified")
    print("[DONE] OLR-037 CERTIFIED")

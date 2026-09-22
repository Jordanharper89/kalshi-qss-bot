import unittest
from qseries_v2.oracle_learning_runtime.olr_036_live_feedback_read_model import LiveCalibrationFeedback
from qseries_v2.oracle_learning_runtime.olr_039_bounded_learning_consumption_envelope import *

class T(unittest.TestCase):
    def test_verifier(self):self.assertTrue(verify_olr_039_bounded_learning_consumption_envelope())
    def test_unmatured_zero(self):
        f=LiveCalibrationFeedback("KX",1,.5,.5,.01,False,"insufficient_history",False,False)
        self.assertEqual(build_bounded_learning_consumption(f).bounded_adjustment,0.0)

if __name__=="__main__":
    print("="*72);print(" OLR-039 CERTIFICATION TEST");print(" BOUNDED LEARNING CONSUMPTION ENVELOPE");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():raise SystemExit(1)
    print("[PASS] Mature-only bounded advisory learning consumption certified")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OLR-039 CERTIFIED")

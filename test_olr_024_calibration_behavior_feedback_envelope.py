import unittest
from qseries_v2.oracle_learning_runtime.olr_023_market_behavior_calibration_profile import MarketBehaviorCalibrationProfile
from qseries_v2.oracle_learning_runtime.olr_024_calibration_behavior_feedback_envelope import *

class T(unittest.TestCase):
    def test_verifier(self):self.assertTrue(verify_olr_024_calibration_behavior_feedback_envelope())
    def test_low_sample_abstains(self):
        p=MarketBehaviorCalibrationProfile("KX",2,.8,1,.1,.2,.2,.04,True,False)
        x=build_calibration_behavior_feedback(p)
        self.assertFalse(x.behavior_signal_available);self.assertEqual(x.bounded_probability_adjustment,0.0)
    def test_bounded(self):
        p=MarketBehaviorCalibrationProfile("KX",100,.1,1,.1,.1,.9,1,True,False)
        self.assertLessEqual(abs(build_calibration_behavior_feedback(p).bounded_probability_adjustment),.05)

if __name__=="__main__":
    print("="*72);print(" OLR-024 CERTIFICATION TEST");print(" CALIBRATION + BEHAVIOR FEEDBACK ENVELOPE");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():raise SystemExit(1)
    print("[PASS] Sample-gated bounded advisory feedback certified")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OLR-024 CERTIFIED")

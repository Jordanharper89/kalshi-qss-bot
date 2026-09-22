import unittest
from qseries_v2.oracle_learning_runtime.olr_022_outcome_calibration_record import OutcomeCalibrationRecord
from qseries_v2.oracle_learning_runtime.olr_023_market_behavior_calibration_profile import *

class T(unittest.TestCase):
    def test_verifier(self):self.assertTrue(verify_olr_023_market_behavior_calibration_profile())
    def test_empty_is_neutral(self):
        x=build_market_behavior_calibration_profile("KX",())
        self.assertEqual(x.reliability_weight,0.0);self.assertEqual(x.calibration_bias,0.0)

if __name__=="__main__":
    print("="*72);print(" OLR-023 CERTIFICATION TEST");print(" MARKET-BEHAVIOR CALIBRATION PROFILE");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():raise SystemExit(1)
    print("[PASS] Outcome calibration + market behavior profile certified")
    print("[DONE] OLR-023 CERTIFIED")

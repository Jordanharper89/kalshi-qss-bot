import unittest
from qseries_v2.oracle_learning_runtime.olr_027_accumulated_calibration_state import AccumulatedCalibrationState
from qseries_v2.oracle_learning_runtime.olr_028_market_behavior_history import *

class T(unittest.TestCase):
    def test_verifier(self):self.assertTrue(verify_olr_028_market_behavior_history())
    def test_immature(self):
        s=AccumulatedCalibrationState("KX",2,.5,.5,.25,.5,0,.04,False,False)
        self.assertEqual(classify_market_behavior(s).behavior_class,"insufficient_history")

if __name__=="__main__":
    print("="*72);print(" OLR-028 CERTIFICATION TEST");print(" MARKET BEHAVIOR HISTORY");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():raise SystemExit(1)
    print("[PASS] Historical market-behavior classification certified")
    print("[DONE] OLR-028 CERTIFIED")

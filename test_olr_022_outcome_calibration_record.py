import unittest
from qseries_v2.oracle_learning_runtime.olr_022_outcome_calibration_record import *

class T(unittest.TestCase):
    def test_verifier(self):self.assertTrue(verify_olr_022_outcome_calibration_record())
    def test_no_probability_abstains(self):self.assertIsNone(build_outcome_calibration_record("KX",{"x":1},"yes"))
    def test_unresolved_abstains(self):self.assertIsNone(build_outcome_calibration_record("KX",{"yes_price":60},""))

if __name__=="__main__":
    print("="*72);print(" OLR-022 CERTIFICATION TEST");print(" OUTCOME CALIBRATION RECORD");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():raise SystemExit(1)
    print("[PASS] Outcome-grounded Brier calibration record certified")
    print("[DONE] OLR-022 CERTIFIED")

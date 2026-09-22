import unittest
from qseries_v2.oracle_continuous_learner.ocl_003_outcome_observation import build_outcome_observation
from qseries_v2.oracle_continuous_learner.ocl_004_learning_event import assemble_learning_event
from qseries_v2.oracle_continuous_learner.ocl_006_calibration_learning import *
class T(unittest.TestCase):
 def e(self):
  o=build_outcome_observation("m","x",1,"t","s","a"*64);return assemble_learning_event("m","b"*64,"c"*64,o)
 def test_verifier(self):self.assertTrue(verify_ocl_006_probability_calibration_learning())
 def test_brier(self):self.assertAlmostEqual(learn_calibration(self.e(),.8,True).brier_score,.04)
 def test_bounds(self):
  with self.assertRaises(ValueError):learn_calibration(self.e(),1.1,True)
if __name__=="__main__":
 print("="*72);print(" OCL-006 CERTIFICATION TEST");print(" PROBABILITY CALIBRATION LEARNING");print("="*72)
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful():raise SystemExit(1)
 print("[PASS] Outcome-grounded probability calibration learning certified");print("[DONE] OCL-006 CERTIFIED")

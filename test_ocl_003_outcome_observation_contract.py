import unittest
from qseries_v2.oracle_continuous_learner.ocl_003_outcome_observation import *
class T(unittest.TestCase):
 def test_verifier(self):self.assertTrue(verify_ocl_003_outcome_observation_contract())
 def test_deterministic(self):
  a=build_outcome_observation("m","settlement",1,"t","s","a"*64);b=build_outcome_observation("m","settlement",1,"t","s","a"*64);self.assertEqual(a.outcome_hash,b.outcome_hash)
 def test_required(self):
  with self.assertRaises(ValueError):build_outcome_observation("","x",1,"t","s","a"*64)
if __name__=="__main__":
 print("="*72);print(" OCL-003 CERTIFICATION TEST");print(" OUTCOME OBSERVATION CONTRACT");print("="*72)
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful():raise SystemExit(1)
 print("[PASS] Immutable outcome-observation contract certified");print("[DONE] OCL-003 CERTIFIED")

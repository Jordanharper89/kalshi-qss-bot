import unittest
from qseries_v2.oracle_continuous_learner.ocl_008_source_calibration_profile import build_source_calibration_profile
from qseries_v2.oracle_continuous_learner.ocl_009_learned_source_state import *
class T(unittest.TestCase):
 def test_verifier(self):self.assertTrue(verify_ocl_009_learned_source_state_snapshot())
 def test_deterministic(self):
  a=build_source_calibration_profile("a",.8,.1,5);b=build_source_calibration_profile("b",.7,.2,5);self.assertEqual(build_learned_source_state_snapshot((a,b)).snapshot_hash,build_learned_source_state_snapshot((b,a)).snapshot_hash)
 def test_duplicate(self):
  a=build_source_calibration_profile("a",.8,.1,5)
  with self.assertRaises(ValueError):build_learned_source_state_snapshot((a,a))
if __name__=="__main__":
 print("="*72);print(" OCL-009 CERTIFICATION TEST");print(" LEARNED SOURCE STATE SNAPSHOT");print("="*72)
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful():raise SystemExit(1)
 print("[PASS] Deterministic learned source-state snapshot certified");print("[DONE] OCL-009 CERTIFIED")

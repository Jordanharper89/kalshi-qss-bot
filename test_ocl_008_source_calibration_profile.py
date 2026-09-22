import unittest
from qseries_v2.oracle_continuous_learner.ocl_008_source_calibration_profile import *
class T(unittest.TestCase):
 def test_verifier(self):self.assertTrue(verify_ocl_008_source_calibration_profile())
 def test_more_evidence_more_weight(self):self.assertGreater(build_source_calibration_profile("s",.8,.1,100).confidence_weight,build_source_calibration_profile("s",.8,.1,1).confidence_weight)
 def test_invalid(self):
  with self.assertRaises(ValueError):build_source_calibration_profile("s",2,.1,1)
if __name__=="__main__":
 print("="*72);print(" OCL-008 CERTIFICATION TEST");print(" SOURCE CALIBRATION PROFILE");print("="*72)
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful():raise SystemExit(1)
 print("[PASS] Reliability/calibration evidence profile certified");print("[DONE] OCL-008 CERTIFIED")

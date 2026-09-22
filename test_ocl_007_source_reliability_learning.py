import unittest
from qseries_v2.oracle_continuous_learner.ocl_007_source_reliability import *
class T(unittest.TestCase):
 def test_verifier(self):self.assertTrue(verify_ocl_007_source_reliability_learning())
 def test_update(self):self.assertGreater(update_source_reliability(None,"s",True).posterior_mean,.5)
 def test_mismatch(self):
  a=update_source_reliability(None,"a",True)
  with self.assertRaises(ValueError):update_source_reliability(a,"b",True)
if __name__=="__main__":
 print("="*72);print(" OCL-007 CERTIFICATION TEST");print(" SOURCE RELIABILITY LEARNING");print("="*72)
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful():raise SystemExit(1)
 print("[PASS] Outcome-grounded Bayesian source reliability learning certified");print("[DONE] OCL-007 CERTIFIED")

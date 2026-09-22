import unittest
from qseries_v2.oracle_continuous_learner.ocl_013_cross_market_dependency import *
class T(unittest.TestCase):
 def test_verifier(self):self.assertTrue(verify_ocl_013_cross_market_dependency_learning())
 def test_positive(self):self.assertGreater(learn_cross_market_dependency("a","b",((1,1),(0,0))).dependency_score,0)
 def test_same_market(self):
  with self.assertRaises(ValueError):learn_cross_market_dependency("a","a",((1,1),))
if __name__=="__main__":
 print("="*72);print(" OCL-013 CERTIFICATION TEST");print(" CROSS-MARKET DEPENDENCY LEARNING");print("="*72)
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful():raise SystemExit(1)
 print("[PASS] Cross-market dependency learning certified without causal overclaim");print("[DONE] OCL-013 CERTIFIED")

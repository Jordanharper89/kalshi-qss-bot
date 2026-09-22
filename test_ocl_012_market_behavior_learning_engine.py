import unittest
from qseries_v2.oracle_continuous_learner.ocl_011_market_behavior_observation import build_market_behavior_observation
from qseries_v2.oracle_continuous_learner.ocl_012_market_behavior_learning import *
class T(unittest.TestCase):
 def o(self,m="m",v=1):return build_market_behavior_observation(m,"r","lag",v,"t"+str(v),"a"*64,"b"*64)
 def test_verifier(self):self.assertTrue(verify_ocl_012_market_behavior_learning_engine())
 def test_count(self):self.assertEqual(learn_market_behavior((self.o(v=1),self.o(v=2))).evidence_count,2)
 def test_mixed(self):
  with self.assertRaises(ValueError):learn_market_behavior((self.o("a"),self.o("b")))
if __name__=="__main__":
 print("="*72);print(" OCL-012 CERTIFICATION TEST");print(" MARKET BEHAVIOR LEARNING ENGINE");print("="*72)
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful():raise SystemExit(1)
 print("[PASS] Repeated market behavior learning certified");print("[DONE] OCL-012 CERTIFIED")

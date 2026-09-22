import unittest
from qseries_v2.oracle_continuous_learner.ocl_014_causal_evidence import *
class T(unittest.TestCase):
 def test_verifier(self):self.assertTrue(verify_ocl_014_causal_evidence_learning())
 def test_uncertain_single_source(self):self.assertEqual(learn_causal_evidence("a","b",(1,),(),1).status,"uncertain")
 def test_counterevidence(self):self.assertLess(learn_causal_evidence("a","b",(.1,),(1,),2).causal_evidence_score,0)
 def test_identity(self):
  with self.assertRaises(ValueError):learn_causal_evidence("a","a",(1,),(),2)
if __name__=="__main__":
 print("="*72);print(" OCL-014 CERTIFICATION TEST");print(" CAUSAL EVIDENCE LEARNING");print("="*72)
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful():raise SystemExit(1)
 print("[PASS] Support/counterevidence causal learning certified");print("[DONE] OCL-014 CERTIFIED")

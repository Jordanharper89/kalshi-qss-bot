import unittest
from qseries_v2.oracle_continuous_learner.ocl_022_learning_maturity import *

class T(unittest.TestCase):
    def test_verifier(self): self.assertTrue(verify_ocl_022_learning_confidence_evidence_maturity())
    def test_contradictions_reduce(self):
        a=evaluate_learning_maturity(100,20,.9,0,.9)
        b=evaluate_learning_maturity(100,20,.9,.8,.9)
        self.assertGreater(a.maturity_score,b.maturity_score)
    def test_bounds(self):
        with self.assertRaises(ValueError): evaluate_learning_maturity(1,1,1.2,0,.5)

if __name__=="__main__":
    print("="*72);print(" OCL-022 CERTIFICATION TEST");print(" LEARNING CONFIDENCE + EVIDENCE MATURITY");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Evidence maturity and learning-confidence evaluation certified")
    print("[DONE] OCL-022 CERTIFIED")

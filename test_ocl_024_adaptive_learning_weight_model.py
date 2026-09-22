import unittest
from qseries_v2.oracle_continuous_learner.ocl_023_meta_learning_performance import evaluate_meta_learning_performance
from qseries_v2.oracle_continuous_learner.ocl_024_adaptive_learning_weight import *

class T(unittest.TestCase):
    def test_verifier(self): self.assertTrue(verify_ocl_024_adaptive_learning_weight_model())
    def test_bounded(self):
        p=evaluate_meta_learning_performance("m",(1,1,1))
        self.assertLessEqual(build_adaptive_learning_weight(p,1,1).adjusted_weight,1)
    def test_bad_weight(self):
        p=evaluate_meta_learning_performance("m",(1,))
        with self.assertRaises(ValueError): build_adaptive_learning_weight(p,2,1)

if __name__=="__main__":
    print("="*72);print(" OCL-024 CERTIFICATION TEST");print(" ADAPTIVE LEARNING WEIGHT MODEL");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Bounded performance/maturity adaptive learning weights certified")
    print("[DONE] OCL-024 CERTIFIED")

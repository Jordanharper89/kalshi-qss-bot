import unittest
from qseries_v2.oracle_scientific_reasoning.osr_001_foundation import build_scientific_reasoning_input
from qseries_v2.oracle_scientific_reasoning.osr_002_hypothesis_formation import *

class T(unittest.TestCase):
    def i(self): return build_scientific_reasoning_input("a"*64,"why")
    def test_verifier(self): self.assertTrue(verify_osr_002_hypothesis_formation())
    def test_prior_bounds(self):
        with self.assertRaises(ValueError): form_hypothesis(self.i(),"h","s","m","f",1)
    def test_falsifier_required(self):
        with self.assertRaises(ValueError): form_hypothesis(self.i(),"h","s","m","",.5)

if __name__=="__main__":
    print("="*72);print(" OSR-002 CERTIFICATION TEST");print(" HYPOTHESIS FORMATION");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Mechanistic falsifiable hypothesis formation certified")
    print("[DONE] OSR-002 CERTIFIED")

import unittest
from qseries_v2.oracle_scientific_reasoning.osr_011_uncertainty_decomposition import *

class T(unittest.TestCase):
    def test_verifier(self): self.assertTrue(verify_osr_011_uncertainty_decomposition_engine())
    def test_dominant(self): self.assertEqual(decompose_uncertainty(.1,.9,.2,.3,.4).dominant_component,"contradiction")
    def test_bounds(self):
        with self.assertRaises(ValueError): decompose_uncertainty(2,0,0,0,0)

if __name__=="__main__":
    print("="*72);print(" OSR-011 CERTIFICATION TEST");print(" UNCERTAINTY DECOMPOSITION ENGINE");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Five-component uncertainty decomposition certified")
    print("[DONE] OSR-011 CERTIFIED")

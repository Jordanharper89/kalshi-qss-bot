import unittest
from qseries_v2.oracle_scientific_reasoning.osr_006_bayesian_update import *

class T(unittest.TestCase):
    def test_verifier(self): self.assertTrue(verify_osr_006_bayesian_belief_update_engine())
    def test_support_increases(self): self.assertGreater(bayesian_update(.4,2).posterior_probability,.4)
    def test_against_decreases(self): self.assertLess(bayesian_update(.4,.5).posterior_probability,.4)
    def test_invalid(self):
        with self.assertRaises(ValueError): bayesian_update(1,2)

if __name__=="__main__":
    print("="*72);print(" OSR-006 CERTIFICATION TEST");print(" BAYESIAN BELIEF UPDATE ENGINE");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Deterministic Bayesian belief updating certified")
    print("[DONE] OSR-006 CERTIFIED")

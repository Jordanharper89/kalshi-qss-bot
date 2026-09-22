import unittest
from qseries_v2.oracle_scientific_reasoning.osr_018_counterfactual_reasoning import *

class T(unittest.TestCase):
    def test_verifier(self): self.assertTrue(verify_osr_018_counterfactual_reasoning_engine())
    def test_direction(self): self.assertEqual(evaluate_counterfactual(1,2,True).direction,"negative")
    def test_unidentifiable(self):
        with self.assertRaises(ValueError): require_identifiable_counterfactual(evaluate_counterfactual(1,0,False))

if __name__=="__main__":
    print("="*72);print(" OSR-018 CERTIFICATION TEST");print(" COUNTERFACTUAL REASONING ENGINE");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Identifiability-aware counterfactual reasoning certified")
    print("[DONE] OSR-018 CERTIFIED")

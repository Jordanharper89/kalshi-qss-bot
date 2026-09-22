import unittest
from qseries_v2.oracle_scientific_reasoning.osr_015_uncertainty_information_adversarial_gate import *

class T(unittest.TestCase):
    def test_verifier(self): self.assertTrue(verify_osr_015_uncertainty_information_adversarial_certification_gate())
    def test_five(self): self.assertEqual(len(certify_osr_011_through_015().builds),5)
    def test_next(self): self.assertEqual(certify_osr_011_through_015().next_capability,"decision_theory_scenario_and_counterfactual_reasoning")

if __name__=="__main__":
    print("="*72);print(" OSR-015 CERTIFICATION TEST");print(" UNCERTAINTY + INFORMATION GAIN + ADVERSARIAL CAPABILITY GATE");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OSR-011 through OSR-015 uncertainty/information/adversarial capability certified")
    print("[PASS] Next capability: decision theory, scenario, and counterfactual reasoning")
    print("[DONE] OSR-015 CERTIFIED")

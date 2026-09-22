import unittest
from qseries_v2.oracle_scientific_reasoning.osr_016_decision_outcome_evaluation import *

class T(unittest.TestCase):
    def test_verifier(self): self.assertTrue(verify_osr_016_decision_theoretic_outcome_evaluation())
    def test_probability_sum(self):
        with self.assertRaises(ValueError):
            evaluate_outcomes((OutcomeState("a",.8,1,0),OutcomeState("b",.8,0,0)))
    def test_risk_penalty(self):
        rows=(OutcomeState("a",1,1,1),)
        self.assertLess(evaluate_outcomes(rows,1).risk_adjusted_value,evaluate_outcomes(rows,0).risk_adjusted_value)

if __name__=="__main__":
    print("="*72);print(" OSR-016 CERTIFICATION TEST");print(" DECISION-THEORETIC OUTCOME EVALUATION");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Risk-adjusted decision-theoretic outcome evaluation certified")
    print("[DONE] OSR-016 CERTIFIED")

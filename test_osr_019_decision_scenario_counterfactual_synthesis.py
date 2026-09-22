import unittest
from qseries_v2.oracle_scientific_reasoning.osr_016_decision_outcome_evaluation import OutcomeState,evaluate_outcomes
from qseries_v2.oracle_scientific_reasoning.osr_017_scenario_branching import make_branch,build_scenario_tree
from qseries_v2.oracle_scientific_reasoning.osr_018_counterfactual_reasoning import evaluate_counterfactual
from qseries_v2.oracle_scientific_reasoning.osr_019_decision_scenario_counterfactual_synthesis import *

class T(unittest.TestCase):
    def test_verifier(self): self.assertTrue(verify_osr_019_decision_scenario_counterfactual_synthesis())
    def test_unidentifiable_abstains(self):
        d=evaluate_outcomes((OutcomeState("a",1,1,0),),0)
        t=build_scenario_tree((make_branch("r",None,1,"r"),make_branch("a","r",1,"a")))
        c=evaluate_counterfactual(1,0,False)
        self.assertTrue(synthesize_decision_scenario_counterfactual(d,t,c).abstain)

if __name__=="__main__":
    print("="*72);print(" OSR-019 CERTIFICATION TEST");print(" DECISION + SCENARIO + COUNTERFACTUAL SYNTHESIS");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Decision/scenario/counterfactual synthesis with abstention certified")
    print("[DONE] OSR-019 CERTIFIED")

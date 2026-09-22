import unittest
from qseries_v2.oracle_scientific_reasoning.osr_007_causal_relationship import *

class T(unittest.TestCase):
    def test_verifier(self): self.assertTrue(verify_osr_007_causal_relationship_evaluation())
    def test_no_temporal_abstains(self):
        c=(CausalCriterion("temporal_precedence",False,1),CausalCriterion("mechanism",True,1))
        self.assertEqual(evaluate_causal_relationship("a","b",c).status,"uncertain")
    def test_counterevidence(self):
        c=(CausalCriterion("temporal_precedence",True,1),CausalCriterion("mechanism",True,1))
        self.assertNotEqual(evaluate_causal_relationship("a","b",c,(1,1)).status,"supported")
    def test_same_identity(self):
        with self.assertRaises(ValueError): evaluate_causal_relationship("a","a",(CausalCriterion("mechanism",True,1),))

if __name__=="__main__":
    print("="*72);print(" OSR-007 CERTIFICATION TEST");print(" CAUSAL RELATIONSHIP EVALUATION");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Temporal/mechanistic causal evaluation with counterevidence certified")
    print("[DONE] OSR-007 CERTIFIED")

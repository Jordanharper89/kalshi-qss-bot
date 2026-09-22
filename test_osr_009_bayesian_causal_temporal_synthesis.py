import unittest
from qseries_v2.oracle_scientific_reasoning.osr_006_bayesian_update import bayesian_update
from qseries_v2.oracle_scientific_reasoning.osr_007_causal_relationship import CausalCriterion,evaluate_causal_relationship
from qseries_v2.oracle_scientific_reasoning.osr_008_temporal_sequence import TemporalEvent,analyze_temporal_sequence
from qseries_v2.oracle_scientific_reasoning.osr_009_reasoning_synthesis import *

class T(unittest.TestCase):
    def components(self,lr=9):
        b=bayesian_update(.5,lr)
        c=evaluate_causal_relationship("c","e",(CausalCriterion("temporal_precedence",True,1),CausalCriterion("mechanism",True,1)))
        t=analyze_temporal_sequence((TemporalEvent("c",1,"a"*64),TemporalEvent("e",2,"b"*64)))
        return b,c,t
    def test_verifier(self): self.assertTrue(verify_osr_009_bayesian_causal_temporal_synthesis())
    def test_abstain_low_bayes(self):
        b,c,t=self.components(.2);self.assertTrue(synthesize_bayesian_causal_temporal(b,c,t,"c","e").abstain)
    def test_temporal_required_for_strength(self):
        b,c,t=self.components();self.assertTrue(synthesize_bayesian_causal_temporal(b,c,t,"e","c").abstain)

if __name__=="__main__":
    print("="*72);print(" OSR-009 CERTIFICATION TEST");print(" BAYESIAN + CAUSAL + TEMPORAL SYNTHESIS");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Bayesian/causal/temporal synthesis with abstention certified")
    print("[DONE] OSR-009 CERTIFIED")

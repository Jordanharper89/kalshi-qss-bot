import unittest
from qseries_v2.oracle_scientific_reasoning.osr_011_uncertainty_decomposition import decompose_uncertainty
from qseries_v2.oracle_scientific_reasoning.osr_013_adversarial_challenge import HypothesisChallenge,challenge_hypothesis
from qseries_v2.oracle_scientific_reasoning.osr_014_alternative_synthesis import *

class T(unittest.TestCase):
    def test_verifier(self): self.assertTrue(verify_osr_014_contradiction_alternative_explanation_synthesis())
    def test_abstain_weak(self):
        u=decompose_uncertainty(.8,.8,.8,.8,.8)
        a=challenge_hypothesis("h",(HypothesisChallenge("c","a",1,1,1),))
        s=synthesize_alternatives(u,a,(AlternativeExplanation("x",.3,.5,.5),))
        self.assertTrue(s.abstain)
    def test_invalid_alt(self):
        u=decompose_uncertainty(.1,.1,.1,.1,.1)
        a=challenge_hypothesis("h",(HypothesisChallenge("c","a",.1,.1,.1),))
        with self.assertRaises(ValueError): synthesize_alternatives(u,a,(AlternativeExplanation("x",2,0,1),))

if __name__=="__main__":
    print("="*72);print(" OSR-014 CERTIFICATION TEST");print(" CONTRADICTION + ALTERNATIVE EXPLANATION SYNTHESIS");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Contradiction/alternative synthesis with abstention certified")
    print("[DONE] OSR-014 CERTIFIED")

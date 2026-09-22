import unittest
from qseries_v2.oracle_scientific_reasoning.osr_001_foundation import build_scientific_reasoning_input
from qseries_v2.oracle_scientific_reasoning.osr_002_hypothesis_formation import form_hypothesis
from qseries_v2.oracle_scientific_reasoning.osr_003_evidence_evaluation import HypothesisEvidenceEvaluation
from qseries_v2.oracle_scientific_reasoning.osr_004_competing_hypotheses import *

class T(unittest.TestCase):
    def pair(self):
        i=build_scientific_reasoning_input("a"*64,"q")
        return (form_hypothesis(i,"a","a","m","f",.5),form_hypothesis(i,"b","b","m","f",.5))
    def test_verifier(self): self.assertTrue(verify_osr_004_competing_hypothesis_analysis())
    def test_abstain_close(self):
        h=self.pair();e=(HypothesisEvidenceEvaluation("a",1,1,0,2,1,"uncertain"),HypothesisEvidenceEvaluation("b",1,1,0,2,1,"uncertain"))
        self.assertTrue(analyze_competing_hypotheses(h,e).abstain)
    def test_two_required(self):
        h=self.pair()[0];e=HypothesisEvidenceEvaluation("a",1,0,1,1,1,"supported")
        with self.assertRaises(ValueError): analyze_competing_hypotheses((h,),(e,))

if __name__=="__main__":
    print("="*72);print(" OSR-004 CERTIFICATION TEST");print(" COMPETING HYPOTHESIS ANALYSIS");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Competing-hypothesis ranking and abstention certified")
    print("[DONE] OSR-004 CERTIFIED")

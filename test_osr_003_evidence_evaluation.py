import unittest
from qseries_v2.oracle_scientific_reasoning.osr_001_foundation import build_scientific_reasoning_input
from qseries_v2.oracle_scientific_reasoning.osr_002_hypothesis_formation import form_hypothesis
from qseries_v2.oracle_scientific_reasoning.osr_003_evidence_evaluation import *

class T(unittest.TestCase):
    def h(self):
        return form_hypothesis(build_scientific_reasoning_input("a"*64,"q"),"h","s","m","f",.5)
    def test_verifier(self): self.assertTrue(verify_osr_003_evidence_evaluation())
    def test_counterevidence(self):
        e=(EvidenceItem("e",False,1,1,1,"b"*64),)
        self.assertEqual(evaluate_hypothesis_evidence(self.h(),e).status,"contradicted")
    def test_duplicate(self):
        e=EvidenceItem("e",True,1,1,1,"b"*64)
        with self.assertRaises(ValueError): evaluate_hypothesis_evidence(self.h(),(e,e))

if __name__=="__main__":
    print("="*72);print(" OSR-003 CERTIFICATION TEST");print(" EVIDENCE EVALUATION");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Reliability/independence/counterevidence evaluation certified")
    print("[DONE] OSR-003 CERTIFIED")

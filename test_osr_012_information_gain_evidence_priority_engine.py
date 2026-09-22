import unittest
from qseries_v2.oracle_scientific_reasoning.osr_012_information_gain_priority import *

class T(unittest.TestCase):
    def test_verifier(self): self.assertTrue(verify_osr_012_information_gain_evidence_priority_engine())
    def test_cost_penalty(self):
        a=EvidenceCandidate("a",.5,1,0);b=EvidenceCandidate("b",.5,1,10)
        self.assertEqual(prioritize_evidence_candidates((b,a))[0].candidate_id,"a")
    def test_duplicate(self):
        a=EvidenceCandidate("a",.5,1,0)
        with self.assertRaises(ValueError): prioritize_evidence_candidates((a,a))

if __name__=="__main__":
    print("="*72);print(" OSR-012 CERTIFICATION TEST");print(" INFORMATION GAIN + EVIDENCE PRIORITY ENGINE");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Expected-information-gain evidence prioritization certified")
    print("[DONE] OSR-012 CERTIFIED")

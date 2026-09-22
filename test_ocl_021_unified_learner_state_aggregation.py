import unittest
from qseries_v2.oracle_continuous_learner.ocl_021_unified_learner_state import *

class T(unittest.TestCase):
    def test_verifier(self): self.assertTrue(verify_ocl_021_unified_learner_state_aggregation())
    def test_total(self):
        x=aggregate_learner_state((LearnerStateComponent("a","a"*64,2,.5),LearnerStateComponent("b","b"*64,3,.7)))
        self.assertEqual(x.total_evidence_count,5)
    def test_duplicate(self):
        a=LearnerStateComponent("a","a"*64,1,.5)
        with self.assertRaises(ValueError): aggregate_learner_state((a,a))

if __name__=="__main__":
    print("="*72);print(" OCL-021 CERTIFICATION TEST");print(" UNIFIED LEARNER STATE AGGREGATION");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Deterministic unified learner-state aggregation certified")
    print("[DONE] OCL-021 CERTIFIED")

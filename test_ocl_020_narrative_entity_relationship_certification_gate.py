import unittest
from qseries_v2.oracle_continuous_learner.ocl_020_narrative_entity_relationship_gate import *

class T(unittest.TestCase):
    def test_verifier(self): self.assertTrue(verify_ocl_020_narrative_entity_relationship_certification_gate())
    def test_five_builds(self): self.assertEqual(len(certify_ocl_016_through_020().builds),5)
    def test_next(self): self.assertEqual(certify_ocl_016_through_020().next_capability,"learner_state_aggregation_and_meta_learning")

if __name__=="__main__":
    print("="*72);print(" OCL-020 CERTIFICATION TEST");print(" NARRATIVE + ENTITY + RELATIONSHIP LEARNING CERTIFICATION GATE");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OCL-016 through OCL-020 narrative/entity/relationship capability certified")
    print("[PASS] Next capability: learner-state aggregation and meta-learning")
    print("[DONE] OCL-020 CERTIFIED")

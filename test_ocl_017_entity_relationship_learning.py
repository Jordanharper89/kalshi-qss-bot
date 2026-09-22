import unittest
from qseries_v2.oracle_continuous_learner.ocl_017_entity_relationship import *

class T(unittest.TestCase):
    def test_verifier(self): self.assertTrue(verify_ocl_017_entity_relationship_learning())
    def test_positive(self): self.assertGreater(learn_entity_relationship("a","b","r",(1,1,0)).relationship_score,0)
    def test_same_entity(self):
        with self.assertRaises(ValueError): learn_entity_relationship("a","a","r",(1,))

if __name__=="__main__":
    print("="*72);print(" OCL-017 CERTIFICATION TEST");print(" ENTITY RELATIONSHIP LEARNING");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Evidence-backed entity relationship learning certified")
    print("[DONE] OCL-017 CERTIFIED")

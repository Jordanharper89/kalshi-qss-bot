import unittest
from qseries_v2.oracle_continuous_learner.ocl_016_entity_learning import *

class T(unittest.TestCase):
    def test_verifier(self):
        self.assertTrue(verify_ocl_016_entity_learning_model())
    def test_deterministic(self):
        a=build_entity_learning_observation("e","person","x",1,"t","a"*64,"b"*64)
        b=build_entity_learning_observation("e","person","x",1,"t","a"*64,"b"*64)
        self.assertEqual(a.observation_hash,b.observation_hash)
    def test_bad_hash(self):
        with self.assertRaises(ValueError):
            build_entity_learning_observation("e","person","x",1,"t","bad","b"*64)

if __name__=="__main__":
    print("="*72);print(" OCL-016 CERTIFICATION TEST");print(" ENTITY LEARNING MODEL");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Outcome-grounded canonical entity learning model certified")
    print("[DONE] OCL-016 CERTIFIED")

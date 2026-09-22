import unittest
from qseries_v2.oracle_continuous_learner.ocl_018_narrative_learning import *

class T(unittest.TestCase):
    def test_verifier(self): self.assertTrue(verify_ocl_018_narrative_learning_engine())
    def test_strengthening(self):
        x=learn_narrative_state((NarrativeObservation("n","support",1,"s1","a"*64),NarrativeObservation("n","support",1,"s2","b"*64)))
        self.assertEqual(x.status,"strengthening")
    def test_mixed(self):
        with self.assertRaises(ValueError):
            learn_narrative_state((NarrativeObservation("a","support",1,"s","a"*64),NarrativeObservation("b","support",1,"s","b"*64)))

if __name__=="__main__":
    print("="*72);print(" OCL-018 CERTIFICATION TEST");print(" NARRATIVE LEARNING ENGINE");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Strengthening/weakening/contested narrative learning certified")
    print("[DONE] OCL-018 CERTIFIED")

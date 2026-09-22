import unittest
from qseries_v2.oracle_continuous_learner.ocl_003_outcome_observation import build_outcome_observation
from qseries_v2.oracle_continuous_learner.ocl_004_learning_event import *
class T(unittest.TestCase):
 def test_verifier(self):self.assertTrue(verify_ocl_004_deterministic_learning_event_assembly())
 def test_subject_mismatch(self):
  o=build_outcome_observation("a","x",1,"t","s","a"*64)
  with self.assertRaises(ValueError):assemble_learning_event("b","b"*64,"c"*64,o)
 def test_replay(self):
  o=build_outcome_observation("m","x",1,"t","s","a"*64);a=assemble_learning_event("m","b"*64,"c"*64,o);b=assemble_learning_event("m","b"*64,"c"*64,o);self.assertEqual(a.event_hash,b.event_hash)
if __name__=="__main__":
 print("="*72);print(" OCL-004 CERTIFICATION TEST");print(" DETERMINISTIC LEARNING EVENT ASSEMBLY");print("="*72)
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful():raise SystemExit(1)
 print("[PASS] Evidence + outcome + lineage learning-event assembly certified");print("[DONE] OCL-004 CERTIFIED")

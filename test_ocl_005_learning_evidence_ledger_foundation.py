import unittest
from qseries_v2.oracle_continuous_learner.ocl_003_outcome_observation import build_outcome_observation
from qseries_v2.oracle_continuous_learner.ocl_004_learning_event import assemble_learning_event
from qseries_v2.oracle_continuous_learner.ocl_005_evidence_ledger import *
class T(unittest.TestCase):
 def event(self,x="m"):
  o=build_outcome_observation(x,"settlement",1,"t","s","a"*64);return assemble_learning_event(x,"b"*64,"c"*64,o)
 def test_verifier(self):self.assertTrue(verify_ocl_005_learning_evidence_ledger_foundation())
 def test_chain(self):
  l=append_learning_event(empty_learning_ledger(),self.event("m1"));l=append_learning_event(l,self.event("m2"));self.assertTrue(verify_learning_ledger(l));self.assertEqual(l.entries[1].parent_hash,l.entries[0].entry_hash)
 def test_next(self):self.assertEqual(build_ocl_005_certification_manifest()["next_capability"],"calibration_and_source_reliability_learning")
if __name__=="__main__":
 print("="*72);print(" OCL-005 CERTIFICATION TEST");print(" LEARNING EVIDENCE LEDGER FOUNDATION");print("="*72)
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful():raise SystemExit(1)
 print("[PASS] Append-only hash-chained learning evidence ledger certified");print("[PASS] Next capability: calibration and source-reliability learning");print("[DONE] OCL-005 CERTIFIED")

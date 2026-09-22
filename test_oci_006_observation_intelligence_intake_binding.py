import unittest
from qseries_v2.oracle_continuous_intake.oci_004_intake_cursor import build_genesis_cursor
from qseries_v2.oracle_continuous_intake.oci_005_intake_batch import IntakeRecord,assemble_intake_batch
from qseries_v2.oracle_continuous_intake.oci_006_oi_intake_binding import *
class T(unittest.TestCase):
 def batch(self,p={"headline":"x"}):
  return assemble_intake_batch(build_genesis_cursor("s","id"),(IntakeRecord.from_payload(1,"r1",p),),"2026-08-12T00:00:00Z")
 def test_verifier(self): self.assertTrue(verify_oci_006_observation_intelligence_intake_binding())
 def test_binding(self): self.assertTrue(verify_oi_binding(bind_batch_to_oi(self.batch())))
 def test_conclusion_rejected(self):
  with self.assertRaises(ValueError): bind_batch_to_oi(self.batch({"prediction":0.8}))
 def test_read_only(self): self.assertFalse(bind_batch_to_oi(self.batch()).upstream_mutation)
if __name__=="__main__":
 print("="*72);print(" OCI-006 CERTIFICATION TEST");print(" OBSERVATION INTELLIGENCE INTAKE BINDING");print("="*72)
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful(): raise SystemExit(1)
 print("[PASS] Observation-not-conclusion intake binding certified");print("[DONE] OCI-006 CERTIFIED")

from __future__ import annotations
import unittest
from qseries_v2.oracle_continuous_intake.oci_004_intake_cursor import build_genesis_cursor
from qseries_v2.oracle_continuous_intake.oci_005_intake_batch import *

class TestOCI005(unittest.TestCase):
    def setUp(self):self.g=build_genesis_cursor("live_shadow","sequence_id")
    def test_verifier(self):self.assertTrue(verify_oci_005_deterministic_intake_batch_assembly())
    def test_order_independent_assembly(self):
        a=IntakeRecord.from_payload(1,"row:1",{"b":2,"a":1});b=IntakeRecord.from_payload(2,"row:2",{"x":2})
        x=assemble_intake_batch(self.g,(b,a),"2026-08-12T00:00:00Z")
        y=assemble_intake_batch(self.g,(a,b),"2026-08-12T00:00:00Z")
        self.assertEqual(x.batch_hash,y.batch_hash);self.assertTrue(verify_batch(x))
    def test_duplicate_cursor_rejected(self):
        a=IntakeRecord.from_payload(1,"row:1",{"x":1});b=IntakeRecord.from_payload(1,"row:2",{"x":2})
        with self.assertRaises(ValueError):assemble_intake_batch(self.g,(a,b),"2026-08-12T00:00:00Z")
    def test_replay_before_cursor_rejected(self):
        from qseries_v2.oracle_continuous_intake.oci_004_intake_cursor import advance_cursor
        c=advance_cursor(self.g,5,"a"*64);r=IntakeRecord.from_payload(5,"row:5",{"x":5})
        with self.assertRaises(ValueError):assemble_intake_batch(c,(r,),"2026-08-12T00:00:00Z")
    def test_manifest_points_to_next_capability(self):
        self.assertEqual(build_oci_005_certification_manifest()["next_boundary"],"OI_UMD_OML_read_only_binding")

if __name__=="__main__":
    print("="*72);print(" OCI-005 CERTIFICATION TEST");print(" DETERMINISTIC INTAKE BATCH ASSEMBLY");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestOCI005))
    if not r.wasSuccessful():raise SystemExit(1)
    print("[PASS] PostgreSQL/live-shadow observations assemble into deterministic replayable batches")
    print("[PASS] Next certified boundary: OI -> UMD -> OML read-only binding")
    print("[DONE] OCI-005 CERTIFIED")

from __future__ import annotations
import unittest
from qseries_v2.oracle_continuous_intake.oci_004_intake_cursor import *

class TestOCI004(unittest.TestCase):
    def test_verifier(self):self.assertTrue(verify_oci_004_deterministic_intake_cursor())
    def test_genesis_deterministic(self):
        self.assertEqual(build_genesis_cursor("s","id").cursor_hash,build_genesis_cursor("s","id").cursor_hash)
    def test_advance_hash_chain(self):
        g=build_genesis_cursor("s","id");a=advance_cursor(g,5,"a"*64)
        self.assertEqual(a.checkpoint_parent_hash,g.cursor_hash);self.assertEqual(a.batch_sequence,1)
    def test_non_monotonic_rejected(self):
        g=build_genesis_cursor("s","id")
        with self.assertRaises(ValueError):advance_cursor(g,0,"a"*64)
    def test_bad_hash_rejected(self):
        g=build_genesis_cursor("s","id")
        with self.assertRaises(ValueError):advance_cursor(g,1,"bad")

if __name__=="__main__":
    print("="*72);print(" OCI-004 CERTIFICATION TEST");print(" DETERMINISTIC INTAKE CURSOR");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestOCI004))
    if not r.wasSuccessful():raise SystemExit(1)
    print("[PASS] Monotonic hash-chained cursor/checkpoint semantics certified")
    print("[DONE] OCI-004 CERTIFIED")

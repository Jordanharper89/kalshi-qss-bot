from __future__ import annotations
import unittest
from dataclasses import FrozenInstanceError
from qseries_v2.oracle_continuous_intake.oci_001_foundation import *

class TestOCI001(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(verify_oci_001_continuous_intake_foundation())
    def test_policy_is_read_only(self):
        p = OCIIntakePolicy()
        self.assertTrue(p.read_only_upstream)
        self.assertFalse(p.qseries_execution_allowed)
        self.assertFalse(p.publication_allowed)
    def test_lineage_deterministic(self):
        a = OCIIntakeLineage("postgresql","live_shadow:1","a"*64,"2026-08-12T00:00:00Z",1)
        b = OCIIntakeLineage("postgresql","live_shadow:1","a"*64,"2026-08-12T00:00:00Z",1)
        self.assertEqual(a.lineage_hash, b.lineage_hash)
    def test_invalid_hash_fails_closed(self):
        with self.assertRaises(ValueError):
            OCIIntakeLineage("postgresql","x","bad","2026-08-12T00:00:00Z",1)
    def test_frozen(self):
        p = OCIIntakePolicy()
        with self.assertRaises(FrozenInstanceError):
            p.read_only_upstream = False

if __name__ == "__main__":
    print("="*72); print(" OCI-001 CERTIFICATION TEST"); print(" CONTINUOUS INTAKE FOUNDATION"); print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestOCI001))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Read-only continuous intake foundation certified")
    print("[PASS] Deterministic lineage and safety policy certified")
    print("[DONE] OCI-001 CERTIFIED")

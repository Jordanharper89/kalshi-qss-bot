from __future__ import annotations
import tempfile, unittest
from pathlib import Path
from qseries_v2.oracle_continuous_intake.oci_002_upstream_boundary import *

class TestOCI002(unittest.TestCase):
    def fixture(self):
        t=tempfile.TemporaryDirectory(); root=Path(t.name)
        for _,rel in REQUIRED_BOUNDARIES:
            p=root/rel; p.mkdir(parents=True); (p/"x.py").write_text("X=1\n",encoding="utf-8")
        (root/LIVE_SHADOW_RUNNERS[0]).write_text("print('x')\n",encoding="utf-8")
        return t,root
    def test_verifier(self): self.assertTrue(verify_oci_002_upstream_boundary_inventory())
    def test_inventory_deterministic(self):
        t,r=self.fixture()
        try:
            a=inspect_upstream_boundaries(r); b=inspect_upstream_boundaries(r)
            self.assertTrue(verify_inventory(a)); self.assertEqual(a.inventory_hash,b.inventory_hash)
            self.assertTrue(all(x.exists for x in a.boundaries))
        finally:t.cleanup()
    def test_missing_boundary_recorded_not_hidden(self):
        t,r=self.fixture()
        try:
            import shutil; shutil.rmtree(r/REQUIRED_BOUNDARIES[0][1])
            inv=inspect_upstream_boundaries(r)
            self.assertFalse(inv.boundaries[0].exists)
        finally:t.cleanup()
    def test_no_upstream_import_or_mutation(self):
        m=build_oci_002_certification_manifest()
        self.assertFalse(m["imports_frozen_upstream"]); self.assertFalse(m["mutates_upstream"])

if __name__=="__main__":
    print("="*72);print(" OCI-002 CERTIFICATION TEST");print(" CERTIFIED UPSTREAM BOUNDARY INVENTORY");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestOCI002))
    if not r.wasSuccessful():raise SystemExit(1)
    print("[PASS] Frozen upstream discovery is structural and read-only")
    print("[DONE] OCI-002 CERTIFIED")

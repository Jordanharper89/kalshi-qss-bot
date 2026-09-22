from __future__ import annotations
import unittest
from qseries_v2.observation_adapter_runtime.oar_016_umd_boundary_resolver import *
class T(unittest.TestCase):
    def test_foundation(self): self.assertTrue(verify_umd_boundary_resolver())
    def test_resolve(self):
        r=UMDBoundaryResolver().resolve((UMDBoundaryCandidate("umd_a","resolve_market","function",5),UMDBoundaryCandidate("umd_b","helper","function",1)))
        self.assertTrue(r.exact_boundary_resolved); self.assertEqual(r.candidates[0].symbol_name,"resolve_market")
if __name__=="__main__":
    print("="*72); print(" OAR-016 CERTIFICATION TEST"); print(" CERTIFIED UMD BOUNDARY RESOLVER"); print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("\n[PASS] Build: OAR-016"); print("[PASS] Deterministic UMD boundary candidate resolution certified"); print("[DONE] OAR-016 CERTIFIED")

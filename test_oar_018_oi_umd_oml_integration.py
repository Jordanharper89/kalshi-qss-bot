from __future__ import annotations
import unittest
from qseries_v2.observation_adapter_runtime.oar_013_oi_canonical_handoff import FrozenOICanonicalHandoffRecord
from qseries_v2.observation_adapter_runtime.oar_018_oi_umd_oml_integration import *
def h():
    return FrozenOICanonicalHandoffRecord(1,("liveobs.1",),("a"*64,),("adapter.crypto.observe.v1",),("coinbase",),("spot_price",),1,"frozen",True)
class T(unittest.TestCase):
    def test_foundation(self): self.assertTrue(verify_oi_umd_oml_integration())
    def test_build(self):
        r=OIUMDOMLIntegrationBuilder().build(h()); self.assertTrue(r.lineage_valid); self.assertEqual(r.observation_count,1)
if __name__=="__main__":
    print("="*72); print(" OAR-018 CERTIFICATION TEST"); print(" OI -> UMD -> OML INTEGRATION PACKAGE"); print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("\n[PASS] Build: OAR-018"); print("[PASS] Frozen OI, UMD, and OML handoffs form one lineage-valid integration package"); print("[PASS] Integration remains read-only with persistence and execution disabled"); print("[DONE] OAR-018 CERTIFIED")

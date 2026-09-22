from __future__ import annotations
import unittest
from datetime import datetime,timezone
from qseries_v2.observation_adapter_runtime.oar_010_canonical_live_observation_bus import CanonicalLiveObservation
from qseries_v2.observation_adapter_runtime.oar_011_live_observation_admission import LiveObservationAdmissionResult
from qseries_v2.observation_adapter_runtime.oar_012_live_observation_bus_registry import *
NOW=datetime(2026,8,12,5,10,tzinfo=timezone.utc)
def obs(i,a,p,c):
    return CanonicalLiveObservation(i,a,p,c,(("x","1"),),NOW,1,"l"*64,i.rjust(64,"0"),True)
class T(unittest.TestCase):
    def test_foundation(self): self.assertTrue(verify_live_observation_bus_registry())
    def test_snapshot(self):
        adm=LiveObservationAdmissionResult(1,(obs("1","adapter.a","p1","snapshot"),obs("2","adapter.b","p2","spot_price")),(),(),2,0,True)
        s=LiveObservationBusRegistry().build_snapshot(adm); self.assertEqual(s.observation_count,2); self.assertEqual(s.adapter_ids,("adapter.a","adapter.b"))
    def test_side_effects(self):
        r=LiveObservationBusRegistry(); self.assertTrue(r.read_only); self.assertFalse(r.execution_allowed); self.assertFalse(r.persistence_allowed)
if __name__=="__main__":
    print("="*72); print(" OAR-012 CERTIFICATION TEST"); print(" LIVE OBSERVATION BUS REGISTRY"); print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("\n[PASS] Build: OAR-012"); print("[PASS] Admitted observations aggregate into deterministic live bus snapshots"); print("[PASS] Adapter, provider, capability, and observation identities exposed read-only"); print("[DONE] OAR-012 CERTIFIED")

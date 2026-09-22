from __future__ import annotations
import unittest
from datetime import datetime,timezone
from qseries_v2.observation_adapters.oad_002_adapter_contract import ObservationAdapterResult
from qseries_v2.observation_adapter_runtime.oar_003_multi_adapter_runner import AdapterRunRecord,MultiAdapterRunResult
from qseries_v2.observation_adapter_runtime.oar_010_canonical_live_observation_bus import *
NOW=datetime(2026,8,12,5,0,tzinfo=timezone.utc)
def rr():
    x=ObservationAdapterResult("r1","adapter.crypto.observe.v1","coinbase","spot_price",({"asset":"BTC","price":"65000"},),NOW,True,None,True,False)
    y=AdapterRunRecord(1,x.adapter_id,x.request_id,x.capability,True,1,None)
    return MultiAdapterRunResult(1,NOW,NOW,(y,),(x,),1,1,0,1,True,False)
class T(unittest.TestCase):
    def test_foundation(self): self.assertTrue(verify_canonical_live_observation_bus())
    def test_materialize(self):
        b=CanonicalLiveObservationBus().materialize(rr()); self.assertEqual(b.observation_count,1); self.assertEqual(b.observations[0].provider_id,"coinbase")
    def test_deterministic(self):
        bus=CanonicalLiveObservationBus(); self.assertEqual(bus.materialize(rr()).batch_hash,bus.materialize(rr()).batch_hash)
if __name__=="__main__":
    print("="*72); print(" OAR-010 CERTIFICATION TEST"); print(" CANONICAL LIVE OBSERVATION BUS"); print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("\n[PASS] Build: OAR-010"); print("[PASS] Canonical live observations and deterministic lineage certified"); print("[DONE] OAR-010 CERTIFIED")

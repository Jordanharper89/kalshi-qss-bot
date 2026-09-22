from __future__ import annotations
import unittest
from datetime import datetime,timezone
from qseries_v2.observation_adapter_runtime.oar_010_canonical_live_observation_bus import CanonicalLiveObservation,CanonicalLiveObservationBatch
from qseries_v2.observation_adapter_runtime.oar_011_live_observation_admission import *
NOW=datetime(2026,8,12,5,5,tzinfo=timezone.utc)
def obs(oid,h):
    return CanonicalLiveObservation(oid,"adapter.a","provider.a","snapshot",(("x","1"),),NOW,1,"l"*64,h,True)
class T(unittest.TestCase):
    def test_foundation(self): self.assertTrue(verify_live_observation_admission())
    def test_admit(self):
        b=CanonicalLiveObservationBatch(1,(obs("o1","a"*64),),1,"b"*64,True); r=LiveObservationAdmissionGate().admit(b); self.assertEqual(r.admitted_count,1)
    def test_duplicate(self):
        a=obs("o1","a"*64); b=obs("o2","a"*64); batch=CanonicalLiveObservationBatch(1,(a,b),2,"c"*64,True); r=LiveObservationAdmissionGate().admit(batch); self.assertEqual(r.admitted_count,1); self.assertEqual(r.rejected_count,1)
if __name__=="__main__":
    print("="*72); print(" OAR-011 CERTIFICATION TEST"); print(" LIVE OBSERVATION ADMISSION GATE"); print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("\n[PASS] Build: OAR-011"); print("[PASS] Canonical live observations admit deterministically"); print("[PASS] Duplicate observation hashes fail closed"); print("[DONE] OAR-011 CERTIFIED")

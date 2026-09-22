from __future__ import annotations
import ast, hashlib
from pathlib import Path
ROOT=Path.cwd().resolve()
PKG=ROOT/"qseries_v2"/"observation_adapter_runtime"
UP=(PKG/"oar_010_canonical_live_observation_bus.py",PKG/"oar_011_live_observation_admission.py",PKG/"oar_009_runtime_health_registry.py",ROOT/"qseries_v2"/"observation_intelligence"/"oi_final_certification_freeze.py")
MOD=PKG/"oar_012_live_observation_bus_registry.py"
INIT=PKG/"__init__.py"
TEST=ROOT/"test_oar_012_live_observation_bus_registry.py"
MODULE=r"""
from __future__ import annotations
from dataclasses import dataclass
from .oar_011_live_observation_admission import LiveObservationAdmissionResult

BUILD_ID="OAR-012"
OAR_012_REVISION="OAR_012_LIVE_OBSERVATION_BUS_REGISTRY_V1"
READ_ONLY=True
EXECUTION_ALLOWED=False
PERSISTENCE_ALLOWED=False

@dataclass(frozen=True,slots=True)
class LiveObservationBusSnapshot:
    iteration_number:int
    observation_ids:tuple[str,...]
    adapter_ids:tuple[str,...]
    provider_ids:tuple[str,...]
    capability_ids:tuple[str,...]
    observation_count:int
    read_only:bool

class LiveObservationBusRegistry:
    read_only=True
    execution_allowed=False
    persistence_allowed=False
    def build_snapshot(self,admission:LiveObservationAdmissionResult)->LiveObservationBusSnapshot:
        if not isinstance(admission,LiveObservationAdmissionResult): raise TypeError("admission must be LiveObservationAdmissionResult")
        observations=tuple(sorted(admission.admitted_observations,key=lambda x:x.observation_id))
        return LiveObservationBusSnapshot(
            admission.iteration_number,
            tuple(x.observation_id for x in observations),
            tuple(sorted({x.adapter_id for x in observations})),
            tuple(sorted({x.provider_id for x in observations})),
            tuple(sorted({x.capability for x in observations})),
            len(observations),
            True,
        )

def verify_live_observation_bus_registry()->bool:
    assert READ_ONLY is True and EXECUTION_ALLOWED is False and PERSISTENCE_ALLOWED is False
    return True
"""
TESTSRC=r"""
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
"""
def sha(x): return hashlib.sha256(x.read_bytes()).hexdigest()
def write(x,t): t=t.lstrip(); ast.parse(t,filename=str(x)); x.parent.mkdir(parents=True,exist_ok=True); x.write_text(t,encoding="utf-8",newline="\n"); print("[PASS] Wrote:",x.relative_to(ROOT))
def main():
    print("="*72); print(" OAR-012 INSTALLER"); print(" LIVE OBSERVATION BUS REGISTRY"); print("="*72); print("[BOOT] Revision: OAR_012_LIVE_OBSERVATION_BUS_REGISTRY_INSTALLER_V1"); print("[ROOT]",ROOT)
    for x in UP:
        if not x.is_file(): raise RuntimeError(f"Certified upstream missing: {x}")
    h={x:sha(x) for x in UP}; backups={x:(x.read_bytes() if x.exists() else None) for x in (MOD,TEST,INIT)}
    try:
        write(MOD,MODULE); write(TEST,TESTSRC)
        cur=INIT.read_text(encoding="utf-8") if INIT.exists() else ""; exp="from .oar_012_live_observation_bus_registry import *"
        if exp not in cur.splitlines():
            if cur and not cur.endswith("\n"): cur+="\n"
            cur+=exp+"\n"; ast.parse(cur,filename=str(INIT)); INIT.write_text(cur,encoding="utf-8",newline="\n")
        for x,e in h.items():
            if sha(x)!=e: raise RuntimeError(f"Certified upstream changed: {x.name}")
        print("[PASS] Certified upstream remained unchanged"); print("[PASS] Deterministic install hash:",hashlib.sha256(MOD.read_bytes()+TEST.read_bytes()).hexdigest()); print("[DONE] OAR-012 INSTALLATION COMPLETE"); return 0
    except Exception:
        for x,b in backups.items():
            if b is None:
                if x.exists(): x.unlink()
            else: x.write_bytes(b)
        raise
if __name__=="__main__": raise SystemExit(main())

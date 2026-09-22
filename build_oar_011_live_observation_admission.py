from __future__ import annotations
import ast, hashlib
from pathlib import Path
ROOT=Path.cwd().resolve()
PKG=ROOT/"qseries_v2"/"observation_adapter_runtime"
UP=(PKG/"oar_009_runtime_health_registry.py",PKG/"oar_010_canonical_live_observation_bus.py",ROOT/"qseries_v2"/"observation_intelligence"/"oi_final_certification_freeze.py")
MOD=PKG/"oar_011_live_observation_admission.py"
INIT=PKG/"__init__.py"
TEST=ROOT/"test_oar_011_live_observation_admission.py"
MODULE=r"""
from __future__ import annotations
from dataclasses import dataclass
from .oar_010_canonical_live_observation_bus import CanonicalLiveObservationBatch

BUILD_ID="OAR-011"
OAR_011_REVISION="OAR_011_LIVE_OBSERVATION_ADMISSION_V1"
READ_ONLY=True
EXECUTION_ALLOWED=False

@dataclass(frozen=True,slots=True)
class LiveObservationAdmissionResult:
    iteration_number:int
    admitted_observations:tuple
    rejected_observation_ids:tuple[str,...]
    duplicate_observation_ids:tuple[str,...]
    admitted_count:int
    rejected_count:int
    read_only:bool

class LiveObservationAdmissionGate:
    read_only=True
    execution_allowed=False
    def admit(self,batch:CanonicalLiveObservationBatch)->LiveObservationAdmissionResult:
        if not isinstance(batch,CanonicalLiveObservationBatch): raise TypeError("batch must be CanonicalLiveObservationBatch")
        seen=set(); admitted=[]; rejected=[]; duplicates=[]
        for obs in batch.observations:
            if obs.observation_hash in seen:
                duplicates.append(obs.observation_id); rejected.append(obs.observation_id); continue
            seen.add(obs.observation_hash)
            if not obs.adapter_id or not obs.provider_id or not obs.capability or not obs.observation_hash:
                rejected.append(obs.observation_id); continue
            admitted.append(obs)
        return LiveObservationAdmissionResult(batch.iteration_number,tuple(admitted),tuple(rejected),tuple(duplicates),len(admitted),len(rejected),True)

def verify_live_observation_admission()->bool:
    assert READ_ONLY is True and EXECUTION_ALLOWED is False
    return True
"""
TESTSRC=r"""
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
"""
def sha(x): return hashlib.sha256(x.read_bytes()).hexdigest()
def write(x,t): t=t.lstrip(); ast.parse(t,filename=str(x)); x.parent.mkdir(parents=True,exist_ok=True); x.write_text(t,encoding="utf-8",newline="\n"); print("[PASS] Wrote:",x.relative_to(ROOT))
def main():
    print("="*72); print(" OAR-011 INSTALLER"); print(" LIVE OBSERVATION ADMISSION GATE"); print("="*72); print("[BOOT] Revision: OAR_011_LIVE_OBSERVATION_ADMISSION_INSTALLER_V1"); print("[ROOT]",ROOT)
    for x in UP:
        if not x.is_file(): raise RuntimeError(f"Certified upstream missing: {x}")
    h={x:sha(x) for x in UP}; backups={x:(x.read_bytes() if x.exists() else None) for x in (MOD,TEST,INIT)}
    try:
        write(MOD,MODULE); write(TEST,TESTSRC)
        cur=INIT.read_text(encoding="utf-8") if INIT.exists() else ""; exp="from .oar_011_live_observation_admission import *"
        if exp not in cur.splitlines():
            if cur and not cur.endswith("\n"): cur+="\n"
            cur+=exp+"\n"; ast.parse(cur,filename=str(INIT)); INIT.write_text(cur,encoding="utf-8",newline="\n")
        for x,e in h.items():
            if sha(x)!=e: raise RuntimeError(f"Certified upstream changed: {x.name}")
        print("[PASS] Certified upstream remained unchanged"); print("[PASS] Deterministic install hash:",hashlib.sha256(MOD.read_bytes()+TEST.read_bytes()).hexdigest()); print("[DONE] OAR-011 INSTALLATION COMPLETE"); return 0
    except Exception:
        for x,b in backups.items():
            if b is None:
                if x.exists(): x.unlink()
            else: x.write_bytes(b)
        raise
if __name__=="__main__": raise SystemExit(main())

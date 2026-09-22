from __future__ import annotations
import ast, hashlib
from pathlib import Path
ROOT=Path.cwd().resolve()
PKG=ROOT/"qseries_v2"/"observation_adapter_runtime"
UP=(PKG/"oar_003_multi_adapter_runner.py",PKG/"oar_009_runtime_health_registry.py",ROOT/"qseries_v2"/"observation_adapters"/"oad_006_default_adapter_bundle.py",ROOT/"qseries_v2"/"observation_intelligence"/"oi_final_certification_freeze.py")
MOD=PKG/"oar_010_canonical_live_observation_bus.py"
INIT=PKG/"__init__.py"
TEST=ROOT/"test_oar_010_canonical_live_observation_bus.py"
MODULE=r"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import timezone
import hashlib,json
from typing import Any,Mapping
from .oar_003_multi_adapter_runner import MultiAdapterRunResult

BUILD_ID="OAR-010"
OAR_010_REVISION="OAR_010_CANONICAL_LIVE_OBSERVATION_BUS_V1"
READ_ONLY=True
EXECUTION_ALLOWED=False
PUBLICATION_ALLOWED=False

def _hash(v:Any)->str:
    return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()

@dataclass(frozen=True,slots=True)
class CanonicalLiveObservation:
    observation_id:str
    adapter_id:str
    provider_id:str
    capability:str
    payload:tuple[tuple[str,str],...]
    observed_at:object
    iteration_number:int
    lineage_hash:str
    observation_hash:str
    read_only:bool

@dataclass(frozen=True,slots=True)
class CanonicalLiveObservationBatch:
    iteration_number:int
    observations:tuple[CanonicalLiveObservation,...]
    observation_count:int
    batch_hash:str
    read_only:bool

class CanonicalLiveObservationBus:
    read_only=True
    execution_allowed=False
    publication_allowed=False
    def materialize(self,run_result:MultiAdapterRunResult)->CanonicalLiveObservationBatch:
        if not isinstance(run_result,MultiAdapterRunResult): raise TypeError("run_result must be MultiAdapterRunResult")
        rows=[]
        for result in run_result.results:
            if not result.success: continue
            for i,raw in enumerate(result.observations,1):
                if not isinstance(raw,Mapping): raw={"value":raw}
                payload=tuple(sorted((str(k),str(v)) for k,v in raw.items()))
                body={"adapter_id":result.adapter_id,"provider_id":result.provider_id,"capability":result.capability,"payload":payload,"observed_at":result.observed_at.astimezone(timezone.utc).isoformat(),"iteration":run_result.iteration_number,"ordinal":i}
                h=_hash(body)
                rows.append(CanonicalLiveObservation("liveobs."+h[:32],result.adapter_id,result.provider_id,result.capability,payload,result.observed_at.astimezone(timezone.utc),run_result.iteration_number,_hash({"request_id":result.request_id,"adapter_id":result.adapter_id,"provider_id":result.provider_id,"capability":result.capability}),h,True))
        rows=tuple(sorted(rows,key=lambda x:(x.adapter_id,x.capability,x.observation_hash)))
        return CanonicalLiveObservationBatch(run_result.iteration_number,rows,len(rows),_hash({"iteration":run_result.iteration_number,"hashes":tuple(x.observation_hash for x in rows)}),True)

def verify_canonical_live_observation_bus()->bool:
    assert READ_ONLY is True and EXECUTION_ALLOWED is False and PUBLICATION_ALLOWED is False
    return True
"""
TESTSRC=r"""
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
"""
def sha(x): return hashlib.sha256(x.read_bytes()).hexdigest()
def write(x,t): t=t.lstrip(); ast.parse(t,filename=str(x)); x.parent.mkdir(parents=True,exist_ok=True); x.write_text(t,encoding="utf-8",newline="\n"); print("[PASS] Wrote:",x.relative_to(ROOT))
def main():
    print("="*72); print(" OAR-010 INSTALLER"); print(" CANONICAL LIVE OBSERVATION BUS"); print("="*72); print("[BOOT] Revision: OAR_010_CANONICAL_LIVE_OBSERVATION_BUS_INSTALLER_V1"); print("[ROOT]",ROOT)
    for x in UP:
        if not x.is_file(): raise RuntimeError(f"Certified upstream missing: {x}")
    h={x:sha(x) for x in UP}; backups={x:(x.read_bytes() if x.exists() else None) for x in (MOD,TEST,INIT)}
    try:
        write(MOD,MODULE); write(TEST,TESTSRC)
        cur=INIT.read_text(encoding="utf-8") if INIT.exists() else ""; exp="from .oar_010_canonical_live_observation_bus import *"
        if exp not in cur.splitlines():
            if cur and not cur.endswith("\n"): cur+="\n"
            cur+=exp+"\n"; ast.parse(cur,filename=str(INIT)); INIT.write_text(cur,encoding="utf-8",newline="\n")
        for x,e in h.items():
            if sha(x)!=e: raise RuntimeError(f"Certified upstream changed: {x.name}")
        print("[PASS] Certified upstream remained unchanged"); print("[PASS] Deterministic install hash:",hashlib.sha256(MOD.read_bytes()+TEST.read_bytes()).hexdigest()); print("[DONE] OAR-010 INSTALLATION COMPLETE"); return 0
    except Exception:
        for x,b in backups.items():
            if b is None:
                if x.exists(): x.unlink()
            else: x.write_bytes(b)
        raise
if __name__=="__main__": raise SystemExit(main())

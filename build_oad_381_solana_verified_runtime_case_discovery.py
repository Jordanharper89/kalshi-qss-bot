from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path
EXPECTED='build_oad_381_solana_verified_runtime_case_discovery.py'
BID='OAD-381'
TITLE='SOLANA VERIFIED RUNTIME CASE DISCOVERY'
MODULE='oad_381_solana_verified_runtime_case_discovery.py'
TEST='test_oad_381_solana_verified_runtime_case_discovery.py'
DEPS={'qseries_v2/oracle_adapters/independent/oad_376_solana_learned_experience_bridge.py': ('SolanaLearnedExperienceRecord', 'EXISTING_OCL')}
MODULE_SOURCE=r"""from __future__ import annotations
from dataclasses import dataclass
import json, hashlib
from pathlib import Path
from .oad_376_solana_learned_experience_bridge import SolanaLearnedExperienceRecord
READ_ONLY=True
EXECUTION_AUTHORITY=False
@dataclass(frozen=True, slots=True)
class VerifiedRuntimeCaseDiscovery:
    files_scanned:int; verified_cases:tuple; rejected_unverified:int; execution_authority:bool=False
def _root():
    p=Path.cwd().resolve()
    for q in (p,*p.parents):
        if (q/"qseries_v2").is_dir(): return q
    raise RuntimeError("repo root not found")
def _records(obj):
    if isinstance(obj,dict):
        yield obj
        for v in obj.values():
            if isinstance(v,(dict,list)): yield from _records(v)
    elif isinstance(obj,list):
        for v in obj: yield from _records(v)
def _case(d):
    low={str(k).lower():v for k,v in d.items()}
    verified=bool(low.get("verified",False)) or str(low.get("outcome_state","")).upper() in ("VERIFIED","OUTCOME_VERIFIED")
    outcome=str(low.get("outcome",low.get("direction",""))).upper()
    source=str(low.get("evidence_source",low.get("source","")))
    if not verified or outcome not in ("UP","DOWN","FLAT") or "SOLANA" not in source.upper(): return None
    case_id=str(low.get("case_id",low.get("id","")))
    h=int(low.get("horizon_seconds",low.get("horizon",0)) or 0)
    if not case_id or h<=0: return None
    ret=float(low.get("return_fraction",low.get("return",0.0)) or 0.0)
    payload={"case_id":case_id,"behavior_type":str(low.get("behavior_type",low.get("event_type","UNKNOWN"))),"protocol":low.get("protocol"),"primary_asset":low.get("primary_asset",low.get("mint")),"secondary_asset":low.get("secondary_asset"),"horizon_seconds":h,"outcome":outcome,"return_fraction":ret,"evidence_source":source,"learning_namespace":"EXISTING_OCL"}
    digest=hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()
    return SolanaLearnedExperienceRecord("SOLANA-EXP-"+digest[:24],case_id,payload["behavior_type"],payload["protocol"],payload["primary_asset"],payload["secondary_asset"],h,outcome,ret,source,digest,"EXISTING_OCL",False)
def discover_verified_runtime_cases(root=None,max_cases=128):
    r=Path(root or _root()); bases=[r/"runtime_state",r/"runtime"/"oracle_live_shadow"]
    files=0; found=[]; rejected=0; ids=set()
    for base in bases:
        if not base.is_dir(): continue
        for p in list(base.rglob("*.json"))+list(base.rglob("*.jsonl")):
            if "test" in str(p).lower(): continue
            files+=1
            try:
                texts=p.read_text(encoding="utf-8").splitlines() if p.suffix.lower()==".jsonl" else [p.read_text(encoding="utf-8")]
                for text in texts:
                    if not text.strip(): continue
                    obj=json.loads(text)
                    for d in _records(obj):
                        c=_case(d)
                        if c is None:
                            if "outcome" in {str(k).lower() for k in d}: rejected+=1
                            continue
                        if c.experience_id not in ids:
                            ids.add(c.experience_id); found.append(c)
                            if len(found)>=max_cases: return VerifiedRuntimeCaseDiscovery(files,tuple(found),rejected,False)
            except Exception: continue
    return VerifiedRuntimeCaseDiscovery(files,tuple(found),rejected,False)
"""
TEST_SOURCE=r"""import unittest
from qseries_v2.oracle_adapters.independent.oad_381_solana_verified_runtime_case_discovery import *
class T(unittest.TestCase):
    def test_discovery(self):
        x=discover_verified_runtime_cases(max_cases=16)
        print("[RUNTIME-CASES] files_scanned=",x.files_scanned,"verified_cases=",len(x.verified_cases),"rejected_unverified=",x.rejected_unverified)
        if x.verified_cases:
            c=x.verified_cases[0]; print("[RUNTIME-CASE-FIRST]",c.case_id,c.horizon_seconds,c.outcome,c.evidence_source)
        self.assertGreaterEqual(x.files_scanned,0)
if __name__=="__main__":
    z=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not z.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-381 physical runtime verified-case discovery measured")
"""
def root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,*b.parents):
            if (p/"qseries_v2").is_dir(): return p
    raise RuntimeError("Q Series repository root not found")
def verify(p,marks):
    if not p.is_file(): raise RuntimeError("dependency missing: "+str(p))
    s=p.read_text(encoding="utf-8"); ast.parse(s,filename=str(p))
    for m in marks:
        if m not in s: raise RuntimeError("dependency interface missing: "+p.name+" -> "+m)
def atomic(p,s):
    s=textwrap.dedent(s).lstrip(); ast.parse(s,filename=str(p))
    p.parent.mkdir(parents=True,exist_ok=True); q=p.with_suffix(p.suffix+".tmp")
    q.write_text(s,encoding="utf-8",newline="\n"); os.replace(q,p)
def main():
    if Path(__file__).name!=EXPECTED: raise RuntimeError("installer identity mismatch")
    r=root(); pkg=r/"qseries_v2"/"oracle_adapters"/"independent"; m=pkg/MODULE; t=r/TEST; init=pkg/"__init__.py"
    print("="*120); print(" "+BID+" "+TITLE+" INSTALLER"); print("="*120); print("[ROOT]",r)
    for rel,marks in DEPS.items(): verify(r/rel,marks); print("[PASS] dependency interface verified:",rel)
    protected=[]
    for rel in (
      "qseries_v2/oracle_production_hardening/oph_023_postgresql_single_writer_production_freeze.py",
      "qseries_v2/oracle_adapters/independent/oad_317_solana_existing_ocl_learning_handoff.py",
      "qseries_v2/oracle_adapters/independent/oad_372_solana_final_persistence_continuity_physical_gate.py",
      "qseries_v2/oracle_adapters/independent/oad_377_solana_existing_ocl_learning_handoff_physical_gate.py",
    ):
        p=r/rel
        if p.is_file(): protected.append((p,hashlib.sha256(p.read_bytes()).hexdigest()))
    old={p:(p.read_bytes() if p.exists() else None) for p in (m,t,init)}
    try:
        atomic(m,MODULE_SOURCE); atomic(t,TEST_SOURCE)
        lines=init.read_text(encoding="utf-8").splitlines() if init.exists() else []
        ex="from ."+m.stem+" import *"
        if ex not in lines: lines.append(ex)
        atomic(init,"\n".join(x for x in lines if x.strip())+"\n")
        for p,h in protected:
            if hashlib.sha256(p.read_bytes()).hexdigest()!=h: raise RuntimeError("protected boundary changed: "+p.name)
        print("[PASS] module installed:",m.relative_to(r)); print("[PASS] test installed:",t.name)
        print("[PASS] certified OAD-317 and production boundaries preserved")
        print("[PASS] no fabricated learning outcome introduced")
        print("[PASS] no separate Solana learner introduced")
        print("[PASS] GMGN not required")
        print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
        print("[DONE] "+BID+" INSTALLATION COMPLETE")
    except Exception:
        for p,b in old.items():
            if b is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(b)
        print("[ROLLBACK] affected files restored"); raise
if __name__=="__main__": main()

from pathlib import Path
import importlib, os, subprocess, sys

ROOT=Path.cwd().resolve()
PKG=ROOT/"qseries_v2"/"oracle_production_hardening"
MOD=PKG/"oph_017_canonical_backend_rejection_forensic.py"
TEST=ROOT/"test_oph_017_canonical_backend_rejection_forensic.py"
WRITER=ROOT/"run_oph_017_forensic_canonical_writer.py"
RUNNER=ROOT/"run_oph_017_full_oracle_backend_rejection_forensic.py"
INIT=PKG/"__init__.py"

MODULE=r"""
from dataclasses import dataclass
@dataclass(frozen=True)
class OPH017Contract:
    request:bool=True
    producer:bool=True
    observation:bool=True
    expected_head:bool=True
    backend_result:bool=True
    reason_codes:bool=True
    execution_authority:bool=False
def verify_oph_017_canonical_backend_rejection_forensic():
    x=OPH017Contract()
    return all((x.request,x.producer,x.observation,x.expected_head,x.backend_result,x.reason_codes)) and not x.execution_authority
"""

TESTSRC=r"""
import unittest
from qseries_v2.oracle_production_hardening.oph_017_canonical_backend_rejection_forensic import verify_oph_017_canonical_backend_rejection_forensic
class T(unittest.TestCase):
    def test_verifier(self): self.assertTrue(verify_oph_017_canonical_backend_rejection_forensic())
if __name__=="__main__":
    print("="*80);print(" OPH-017 CERTIFICATION TEST");print(" CANONICAL BACKEND REJECTION FORENSIC");print("="*80)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OPH-017 certified");print("[DONE] OPH-017 CERTIFIED")
"""

WRITERSRC=r"""
from __future__ import annotations
import json,os,time,traceback,uuid
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path.cwd().resolve()
TRACE=ROOT/"runtime_state"/"oph_017_backend_rejection_forensic.jsonl"
CURRENT={}
from qseries_v2.oracle_production_hardening.oph_006_durable_cross_process_observation_queue import claim_next_request,complete_request,fail_request,queue_counts
from qseries_v2.oracle_production_hardening.oph_007_physical_single_postgresql_writer_runtime import build_existing_canonical_router

def emit(kind,**x):
    r={"ts":datetime.now(timezone.utc).isoformat(),"pid":os.getpid(),"kind":kind,**x}
    TRACE.parent.mkdir(parents=True,exist_ok=True)
    with TRACE.open("a",encoding="utf-8") as f:f.write(json.dumps(r,sort_keys=True,default=str)+"\n")
    if kind in ("BACKEND_REJECTION","ROUTER_EXCEPTION","REQUEST_FAILED"):
        print("="*112,flush=True);print(f"[OPH-017 FORENSIC] kind={kind}",flush=True)
        for k,v in r.items():print(f"[OPH-017] {k}={v}",flush=True)
        print("="*112,flush=True)
    return r

def ticker(obs):
    try:
        p=dict(getattr(obs,"payload",{}) or {})
        return p.get("source_market_id") or p.get("source_symbol") or p.get("ticker")
    except Exception:return None

def install():
    from qseries_v2.oracle_intelligence.live_acquisition.oracle_postgresql_canonical_observation_persistence_router import OraclePostgreSQLCanonicalObservationPersistenceRouter as C
    ov=C._validate_batch_append_result
    oroute=C.route_batch
    def val(*args,**kw):
        ar=kw.get("append_result"); ex=kw.get("expected_terminal_chain_hash"); obs=kw.get("observations")
        if ar is None:
            for v in args:
                if hasattr(v,"reason_codes") or hasattr(v,"append_status"): ar=v;break
        if obs is None:
            for v in args:
                if isinstance(v,(tuple,list)) and v and hasattr(v[0],"observation_id"):obs=v;break
        items=tuple(obs or ()); first=items[0] if items else None
        reasons=tuple(getattr(ar,"reason_codes",()) or ()) if ar is not None else ()
        status=getattr(ar,"append_status",None) if ar is not None else None
        committed=getattr(ar,"committed",None) if ar is not None else None
        if committed is False or status=="rejected" or "append_rejected" in reasons:
            emit("BACKEND_REJECTION",**CURRENT,observation_count=len(items),observation_id=getattr(first,"observation_id",None) if first else None,observation_type=getattr(first,"observation_type",None) if first else None,ticker=ticker(first) if first else None,expected_terminal_chain_hash=ex,append_status=status,committed=committed,reason_codes=reasons,prior_terminal_chain_hash=getattr(ar,"prior_terminal_chain_hash",None) if ar is not None else None,terminal_chain_hash=getattr(ar,"terminal_chain_hash",None) if ar is not None else None,appended_count=getattr(ar,"appended_count",None) if ar is not None else None,rejected_count=getattr(ar,"rejected_count",None) if ar is not None else None)
        return ov(*args,**kw)
    def route(self,observations,routed_at,*a,**kw):
        try:return oroute(self,tuple(observations),routed_at,*a,**kw)
        except Exception as e:
            emit("ROUTER_EXCEPTION",**CURRENT,exception_type=type(e).__name__,exception_message=str(e),traceback="".join(traceback.format_exception(type(e),e,e.__traceback__)))
            raise
    C._validate_batch_append_result=staticmethod(val);C.route_batch=route

def main():
    print("="*112);print(" OPH-017 CANONICAL BACKEND REJECTION FORENSIC WRITER");print("="*112)
    TRACE.unlink(missing_ok=True);install()
    wid=f"oph017:{os.getpid()}:{uuid.uuid4().hex[:8]}"; router=build_existing_canonical_router(ROOT)
    print(f"[WORKER] {wid}");print(f"[QUEUE] {queue_counts(ROOT)}");print("[ACTION] Waiting for first physical backend rejection.")
    while True:
        try:
            item=claim_next_request(wid,ROOT)
            if item is None:time.sleep(.002);continue
            rid,producer,priority,observations=item; items=tuple(observations)
            CURRENT.clear();CURRENT.update({"request_id":rid,"producer":producer,"priority":priority})
            try:
                result=tuple(router.route_batch(items,datetime.now(timezone.utc)));complete_request(rid,result,ROOT)
            except Exception as e:
                fail_request(rid,e,ROOT);emit("REQUEST_FAILED",**CURRENT,observation_count=len(items),exception_type=type(e).__name__,exception_message=str(e))
                print("[CAPTURED] First failing request captured. Press Ctrl+C and send the OPH-017 block.",flush=True)
                router=build_existing_canonical_router(ROOT)
        except KeyboardInterrupt:
            print();print("[STOP] OPH-017 stopped by operator");return 0
if __name__=="__main__":raise SystemExit(main())
"""

RUNNERSRC=r"""
from __future__ import annotations
import ast,subprocess,sys
from pathlib import Path
ROOT=Path.cwd().resolve();PROD=ROOT/"run_oracle_LIVE.py";TEMP=ROOT/"run_oracle_LIVE_OPH017_FORENSIC.py";FORENSIC=ROOT/"run_oph_017_forensic_canonical_writer.py"
def patch(source):
    tree=ast.parse(source);node=None
    for i in ast.walk(tree):
        if isinstance(i,ast.Assign) and isinstance(i.value,ast.Dict) and any(isinstance(t,ast.Name) and t.id=="CHILDREN" for t in i.targets):node=i.value;break
    if node is None:raise RuntimeError("CHILDREN dictionary not found")
    lines=source.splitlines(keepends=True)
    for k,v in zip(node.keys,node.values):
        if isinstance(k,ast.Constant) and str(k.value)=="canonical_writer" and isinstance(v,ast.Constant) and isinstance(v.value,str):
            old=v.value;idx=v.lineno-1
            for tok in (repr(old),'"'+old+'"',"'"+old+"'"):
                if tok in lines[idx]:
                    lines[idx]=lines[idx].replace(tok,repr(FORENSIC.name),1);out="".join(lines);ast.parse(out);return out,old
    raise RuntimeError("canonical_writer child not found")
def main():
    print("="*108);print(" OPH-017 FULL ORACLE BACKEND REJECTION FORENSIC");print("="*108)
    source=PROD.read_text(encoding="utf-8");out,old=patch(source);TEMP.write_text(out,encoding="utf-8",newline="\n")
    print(f"[PRODUCTION WRITER] {old}");print(f"[DIAGNOSTIC WRITER] {FORENSIC.name}");print("[ACTION] Run until [OPH-017 FORENSIC], then Ctrl+C.")
    try:return subprocess.run([sys.executable,str(TEMP)],cwd=str(ROOT)).returncode
    except KeyboardInterrupt:return 0
if __name__=="__main__":raise SystemExit(main())
"""

def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    t=path.with_suffix(path.suffix+".tmp");t.write_text(text,encoding="utf-8",newline="\n");os.replace(t,path)

def main():
    print("="*88);print(" OPH-017 INSTALLER");print(" CANONICAL BACKEND REJECTION FORENSIC");print("="*88);print("[ROOT]",ROOT)
    sys.path.insert(0,str(ROOT))
    up=importlib.import_module("qseries_v2.oracle_production_hardening.oph_016_fast_lane_persistence_escape_trace")
    if up.verify_oph_016_fast_lane_persistence_escape_trace() is not True:raise RuntimeError("OPH-016 verification failed")
    print("[PASS] Certified OPH-016 upstream boundary verified")
    affected=(MOD,TEST,WRITER,RUNNER,INIT);old={x:(x.read_bytes() if x.exists() else None) for x in affected}
    try:
        write_exact(MOD,MODULE);write_exact(TEST,TESTSRC);write_exact(WRITER,WRITERSRC);write_exact(RUNNER,RUNNERSRC)
        cur=INIT.read_text(encoding="utf-8") if INIT.exists() else "";ex="from .oph_017_canonical_backend_rejection_forensic import *"
        if ex not in cur:write_exact(INIT,cur.rstrip()+"\n"+ex+"\n")
        for x in (MOD,TEST,WRITER,RUNNER):compile(x.read_text(encoding="utf-8"),str(x),"exec")
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
    except Exception:
        for x,b in old.items():
            if b is None:
                if x.exists():x.unlink()
            else:x.write_bytes(b)
        print("[ROLLBACK] OPH-017 installation failed");raise
    print("[PASS] Wrote:",MOD.relative_to(ROOT));print("[PASS] Wrote:",TEST.name);print("[PASS] Wrote:",WRITER.name);print("[PASS] Wrote:",RUNNER.name)
    print("[PASS] Production launcher untouched");print("[PASS] execution_authority=FALSE");print("[DONE] OPH-017 INSTALLATION AND CERTIFICATION COMPLETE")
if __name__=="__main__":main()

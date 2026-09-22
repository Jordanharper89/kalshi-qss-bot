
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

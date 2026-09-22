from __future__ import annotations
import json,os,runpy
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.cwd().resolve()
TRACE=ROOT/"runtime_state"/"opc_036_persistence_collision_trace.jsonl"
WRITER='FAST_LANE'
UNDERLYING='run_oracle_priority_fast_lane_child.py'

def utcnow():
    return datetime.now(timezone.utc).isoformat()

def emit(kind,**payload):
    record={
        "ts":utcnow(),
        "pid":os.getpid(),
        "writer":WRITER,
        "kind":kind,
        **payload,
    }
    TRACE.parent.mkdir(parents=True,exist_ok=True)
    with TRACE.open("a",encoding="utf-8") as f:
        f.write(json.dumps(record,sort_keys=True,default=str)+"\n")
    if kind in ("REJECTED_APPEND","ROUTER_EXCEPTION"):
        print("="*104,flush=True)
        print(f"[OPC-036 COLLISION] writer={WRITER} kind={kind}",flush=True)
        for k,v in record.items():
            print(f"[OPC-036] {k}={v}",flush=True)
        print("="*104,flush=True)

def arbiter_snapshot():
    runtime=ROOT/"runtime_state"
    intent=runtime/"oracle_fast_lane_persistence_intent.json"
    out={"fast_intent_present":intent.exists()}
    if intent.exists():
        try:
            out["fast_intent"]=json.loads(intent.read_text(encoding="utf-8"))
        except Exception as exc:
            out["fast_intent_error"]=f"{type(exc).__name__}: {exc}"
    return out

from qseries_v2.oracle_intelligence.live_acquisition.oracle_postgresql_canonical_observation_persistence_router import (
    OraclePostgreSQLCanonicalObservationPersistenceRouter,
)

cls=OraclePostgreSQLCanonicalObservationPersistenceRouter
original_validate=cls._validate_batch_append_result
original_route=cls.route_batch

def traced_validate(self,*args,**kwargs):
    append_result=kwargs.get("append_result")
    expected=kwargs.get("expected_terminal_chain_hash")
    observations=kwargs.get("observations") or ()

    reason_codes=tuple(getattr(append_result,"reason_codes",()) or ()) if append_result is not None else ()
    committed=getattr(append_result,"committed",None) if append_result is not None else None
    status=getattr(append_result,"append_status",None) if append_result is not None else None

    if committed is False or status=="rejected" or reason_codes:
        first=None
        try:
            first=tuple(observations)[0] if observations else None
        except Exception:
            pass

        payload={}
        if first is not None:
            try:
                payload=dict(getattr(first,"payload",{}) or {})
            except Exception:
                pass

        emit(
            "REJECTED_APPEND",
            observation_id=getattr(first,"observation_id",None) if first is not None else None,
            observation_type=getattr(first,"observation_type",None) if first is not None else None,
            ticker=payload.get("source_market_id") or payload.get("source_symbol"),
            expected_terminal_chain_hash=expected,
            prior_terminal_chain_hash=getattr(append_result,"prior_terminal_chain_hash",None) if append_result is not None else None,
            terminal_chain_hash=getattr(append_result,"terminal_chain_hash",None) if append_result is not None else None,
            append_status=status,
            committed=committed,
            reason_codes=reason_codes,
            appended_count=getattr(append_result,"appended_count",None) if append_result is not None else None,
            rejected_count=getattr(append_result,"rejected_count",None) if append_result is not None else None,
            arbiter=arbiter_snapshot(),
        )

    return original_validate(self,*args,**kwargs)

def traced_route(self,observations,routed_at,*args,**kwargs):
    try:
        return original_route(self,observations,routed_at,*args,**kwargs)
    except Exception as exc:
        emit(
            "ROUTER_EXCEPTION",
            exception_type=type(exc).__name__,
            exception_message=str(exc),
            arbiter=arbiter_snapshot(),
        )
        raise

cls._validate_batch_append_result=traced_validate
cls.route_batch=traced_route

emit("WRAPPER_STARTED",underlying=UNDERLYING)
runpy.run_path(str(ROOT/UNDERLYING),run_name="__main__")

from __future__ import annotations

import ast
import json
import subprocess
import sys
from pathlib import Path

ROOT=Path.cwd().resolve()
RUNTIME=ROOT/"runtime_state"
RUNTIME.mkdir(parents=True,exist_ok=True)

TRACE=RUNTIME/"opc_036_persistence_collision_trace.jsonl"
TMP_LAUNCHER=ROOT/"run_oracle_LIVE_OPC036_DIAGNOSTIC.py"
FAST_WRAPPER=ROOT/"run_opc_036_trace_fast_lane_child.py"
COVERAGE_WRAPPER=ROOT/"run_opc_036_trace_coverage_child.py"

LINE="="*104
WRAPPER_TEMPLATE='from __future__ import annotations\nimport json,os,runpy\nfrom datetime import datetime,timezone\nfrom pathlib import Path\n\nROOT=Path.cwd().resolve()\nTRACE=ROOT/"runtime_state"/"opc_036_persistence_collision_trace.jsonl"\nWRITER=__WRITER__\nUNDERLYING=__UNDERLYING__\n\ndef utcnow():\n    return datetime.now(timezone.utc).isoformat()\n\ndef emit(kind,**payload):\n    record={\n        "ts":utcnow(),\n        "pid":os.getpid(),\n        "writer":WRITER,\n        "kind":kind,\n        **payload,\n    }\n    TRACE.parent.mkdir(parents=True,exist_ok=True)\n    with TRACE.open("a",encoding="utf-8") as f:\n        f.write(json.dumps(record,sort_keys=True,default=str)+"\\n")\n    if kind in ("REJECTED_APPEND","ROUTER_EXCEPTION"):\n        print("="*104,flush=True)\n        print(f"[OPC-036 COLLISION] writer={WRITER} kind={kind}",flush=True)\n        for k,v in record.items():\n            print(f"[OPC-036] {k}={v}",flush=True)\n        print("="*104,flush=True)\n\ndef arbiter_snapshot():\n    runtime=ROOT/"runtime_state"\n    intent=runtime/"oracle_fast_lane_persistence_intent.json"\n    out={"fast_intent_present":intent.exists()}\n    if intent.exists():\n        try:\n            out["fast_intent"]=json.loads(intent.read_text(encoding="utf-8"))\n        except Exception as exc:\n            out["fast_intent_error"]=f"{type(exc).__name__}: {exc}"\n    return out\n\nfrom qseries_v2.oracle_intelligence.live_acquisition.oracle_postgresql_canonical_observation_persistence_router import (\n    OraclePostgreSQLCanonicalObservationPersistenceRouter,\n)\n\ncls=OraclePostgreSQLCanonicalObservationPersistenceRouter\noriginal_validate=cls._validate_batch_append_result\noriginal_route=cls.route_batch\n\ndef traced_validate(self,*args,**kwargs):\n    append_result=kwargs.get("append_result")\n    expected=kwargs.get("expected_terminal_chain_hash")\n    observations=kwargs.get("observations") or ()\n\n    reason_codes=tuple(getattr(append_result,"reason_codes",()) or ()) if append_result is not None else ()\n    committed=getattr(append_result,"committed",None) if append_result is not None else None\n    status=getattr(append_result,"append_status",None) if append_result is not None else None\n\n    if committed is False or status=="rejected" or reason_codes:\n        first=None\n        try:\n            first=tuple(observations)[0] if observations else None\n        except Exception:\n            pass\n\n        payload={}\n        if first is not None:\n            try:\n                payload=dict(getattr(first,"payload",{}) or {})\n            except Exception:\n                pass\n\n        emit(\n            "REJECTED_APPEND",\n            observation_id=getattr(first,"observation_id",None) if first is not None else None,\n            observation_type=getattr(first,"observation_type",None) if first is not None else None,\n            ticker=payload.get("source_market_id") or payload.get("source_symbol"),\n            expected_terminal_chain_hash=expected,\n            prior_terminal_chain_hash=getattr(append_result,"prior_terminal_chain_hash",None) if append_result is not None else None,\n            terminal_chain_hash=getattr(append_result,"terminal_chain_hash",None) if append_result is not None else None,\n            append_status=status,\n            committed=committed,\n            reason_codes=reason_codes,\n            appended_count=getattr(append_result,"appended_count",None) if append_result is not None else None,\n            rejected_count=getattr(append_result,"rejected_count",None) if append_result is not None else None,\n            arbiter=arbiter_snapshot(),\n        )\n\n    return original_validate(self,*args,**kwargs)\n\ndef traced_route(self,observations,routed_at,*args,**kwargs):\n    try:\n        return original_route(self,observations,routed_at,*args,**kwargs)\n    except Exception as exc:\n        emit(\n            "ROUTER_EXCEPTION",\n            exception_type=type(exc).__name__,\n            exception_message=str(exc),\n            arbiter=arbiter_snapshot(),\n        )\n        raise\n\ncls._validate_batch_append_result=traced_validate\ncls.route_batch=traced_route\n\nemit("WRAPPER_STARTED",underlying=UNDERLYING)\nrunpy.run_path(str(ROOT/UNDERLYING),run_name="__main__")\n'

def read_children(source):
    tree=ast.parse(source)
    for item in ast.walk(tree):
        if isinstance(item,ast.Assign) and isinstance(item.value,ast.Dict):
            if any(isinstance(t,ast.Name) and t.id=="CHILDREN" for t in item.targets):
                out={}
                for k,v in zip(item.value.keys,item.value.values):
                    if isinstance(k,ast.Constant) and isinstance(v,ast.Constant):
                        out[str(k.value)]=str(v.value)
                return out
    raise RuntimeError("CHILDREN dictionary not found")

def patch_child(source,child,new_value):
    tree=ast.parse(source)
    node=None
    for item in ast.walk(tree):
        if isinstance(item,ast.Assign) and isinstance(item.value,ast.Dict):
            if any(isinstance(t,ast.Name) and t.id=="CHILDREN" for t in item.targets):
                node=item.value
                break
    if node is None:
        raise RuntimeError("CHILDREN dictionary not found")

    lines=source.splitlines(keepends=True)

    for k,v in zip(node.keys,node.values):
        if isinstance(k,ast.Constant) and str(k.value)==child:
            if not isinstance(v,ast.Constant) or not isinstance(v.value,str):
                raise RuntimeError(f"{child} runner is not a literal string")
            old=v.value
            idx=v.lineno-1
            line=lines[idx]
            for token in (repr(old),'"'+old+'"',"'"+old+"'"):
                if token in line:
                    lines[idx]=line.replace(token,repr(new_value),1)
                    patched="".join(lines)
                    ast.parse(patched)
                    return patched
            raise RuntimeError(f"could not patch {child}")

    raise RuntimeError(f"{child} child not found")

def make_wrapper(writer,underlying):
    return (
        WRAPPER_TEMPLATE
        .replace("__WRITER__",repr(writer))
        .replace("__UNDERLYING__",repr(underlying))
    )

def summarize():
    if not TRACE.exists():
        print("[TRACE] No trace file created")
        return
    lines=TRACE.read_text(encoding="utf-8",errors="ignore").splitlines()
    hits=[]
    for line in lines:
        try:
            obj=json.loads(line)
        except Exception:
            continue
        if obj.get("kind") in ("REJECTED_APPEND","ROUTER_EXCEPTION"):
            hits.append(obj)
    print(f"[TRACE] records={len(lines)} collision_records={len(hits)}")
    for obj in hits[-10:]:
        print("-"*104)
        for k,v in obj.items():
            print(f"[TRACE] {k}={v}")

def main():
    print(LINE)
    print(" OPC-036 FULL ORACLE PERSISTENCE COLLISION TRACE")
    print(" TEMPORARY DIAGNOSTIC LAUNCHER — PRODUCTION FILES UNTOUCHED")
    print(LINE)

    launcher=ROOT/"run_oracle_LIVE.py"
    if not launcher.exists():
        raise SystemExit("run_oracle_LIVE.py missing")

    source=launcher.read_text(encoding="utf-8")
    children=read_children(source)
    fast=children.get("fast_lane")
    coverage=children.get("coverage")

    if not fast or not coverage:
        raise SystemExit("fast_lane or coverage child missing")

    print(f"[DISCOVERY] fast_lane={fast}")
    print(f"[DISCOVERY] coverage={coverage}")

    TRACE.unlink(missing_ok=True)

    FAST_WRAPPER.write_text(make_wrapper("FAST_LANE",fast),encoding="utf-8",newline="\n")
    COVERAGE_WRAPPER.write_text(make_wrapper("COVERAGE",coverage),encoding="utf-8",newline="\n")

    diagnostic=patch_child(source,"fast_lane",FAST_WRAPPER.name)
    diagnostic=patch_child(diagnostic,"coverage",COVERAGE_WRAPPER.name)
    TMP_LAUNCHER.write_text(diagnostic,encoding="utf-8",newline="\n")

    compile(FAST_WRAPPER.read_text(encoding="utf-8"),str(FAST_WRAPPER),"exec")
    compile(COVERAGE_WRAPPER.read_text(encoding="utf-8"),str(COVERAGE_WRAPPER),"exec")
    compile(TMP_LAUNCHER.read_text(encoding="utf-8"),str(TMP_LAUNCHER),"exec")

    print("[PASS] Temporary diagnostic launcher created")
    print("[PASS] Production run_oracle_LIVE.py untouched")
    print(f"[TRACE FILE] {TRACE.relative_to(ROOT)}")
    print("[ACTION] Let it run until [OPC-036 COLLISION] appears, then press Ctrl+C")

    rc=0
    try:
        rc=subprocess.run([sys.executable,str(TMP_LAUNCHER)],cwd=str(ROOT)).returncode
    except KeyboardInterrupt:
        print()
        print("[STOP] Diagnostic stopped by operator")

    print(LINE)
    print(" OPC-036 COLLISION TRACE SUMMARY")
    print(LINE)
    summarize()
    print("[PASS] Production launcher was not modified")
    print("[PASS] Frozen OLA/OLR source was not modified")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OPC-036 FULL ORACLE COLLISION TRACE COMPLETE")
    return rc

if __name__=="__main__":
    raise SystemExit(main())

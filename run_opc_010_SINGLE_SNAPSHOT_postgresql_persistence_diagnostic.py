from __future__ import annotations

import inspect
import traceback
from pathlib import Path
from datetime import datetime, timezone

ROOT=Path.cwd().resolve()
LINE="="*96

def main():
    print(LINE)
    print(" OPC-010 SINGLE-SNAPSHOT POSTGRESQL PERSISTENCE DIAGNOSTIC")
    print(" RUNTIME INSTRUMENTATION ONLY — NO SOURCE FILE MODIFICATIONS")
    print(LINE)

    from qseries_v2.oracle_pre_settlement_coverage.opc_002_bounded_open_market_sampler import (
        sample_live_open_markets,
    )
    from qseries_v2.oracle_pre_settlement_coverage.opc_003_canonical_observation_coverage_read_model import (
        read_recent_canonical_tickers,
    )
    from qseries_v2.oracle_pre_settlement_coverage.opc_006_universal_market_snapshot_canonicalizer import (
        build_universal_market_snapshot,
    )
    from qseries_v2.oracle_pre_settlement_coverage.opc_008_ola_postgresql_snapshot_persistence_bridge import (
        build_opc_postgresql_router,
    )

    sample=sample_live_open_markets(ROOT,pages=1)
    recent=read_recent_canonical_tickers(ROOT,24,250000)

    target=None
    for ticker in sample.markets:
        if ticker not in recent:
            target=ticker
            break

    if not target:
        print("[ABSTAIN] No uncovered market found in the current bounded sample.")
        print("[DONE] Nothing to diagnose.")
        return 0

    # Fetch the full market row for the selected ticker using the same certified REST path.
    from qseries_v2.oracle_adapters.kalshi.oad_021_credentials import load_kalshi_credentials
    from qseries_v2.oracle_adapters.kalshi.oad_022_rest_transport import kalshi_rest_get

    credentials=load_kalshi_credentials()
    response=kalshi_rest_get(
        credentials,
        "/markets/"+target,
        {},
        15,
    )
    body=response.body or {}
    market=body.get("market") if isinstance(body,dict) else None
    if not isinstance(market,dict):
        # Fallback: get one open page and locate the ticker.
        response=kalshi_rest_get(
            credentials,
            "/markets",
            {"limit":1000,"status":"open"},
            15,
        )
        markets=(response.body or {}).get("markets",[]) or []
        market=next((x for x in markets if isinstance(x,dict) and str(x.get("ticker") or "")==target),None)

    if not isinstance(market,dict):
        print(f"[ERROR] Could not recover full market row for {target}")
        return 2

    now=datetime.now(timezone.utc)
    observation=build_universal_market_snapshot(
        market,
        acquired_at=now,
        batch_id="batch.opc.persistence.diagnostic."+now.strftime("%Y%m%dT%H%M%S"),
    )

    print(f"[TARGET] ticker={target}")
    print(f"[CANONICAL] observation_id={observation.observation_id}")
    print(f"[CANONICAL] content_hash={observation.content_hash}")
    print(f"[CANONICAL] observation_type={observation.observation_type}")
    print(f"[CANONICAL] read_only={observation.read_only}")
    print(f"[CANONICAL] execution_allowed={observation.execution_allowed}")
    print(f"[CANONICAL] payload_keys={tuple(sorted(dict(observation.payload).keys()))}")

    router=build_opc_postgresql_router(ROOT)

    print("-"*96)
    print("[ROUTER] class=",type(router).__module__+"."+type(router).__name__)

    router_dict=getattr(router,"__dict__",{})
    print("[ROUTER] attributes=",tuple(sorted(router_dict.keys())))

    backend=None
    for name,value in router_dict.items():
        if "backend" in name.lower() or "persist" in name.lower():
            if value is not None and not isinstance(value,(str,int,float,bool,dict,list,tuple,set)):
                backend=value
                print(f"[ROUTER] backend_candidate={name} -> {type(value).__module__}.{type(value).__name__}")
                break

    if backend is not None:
        print("[BACKEND] attributes=",tuple(sorted(getattr(backend,"__dict__",{}).keys())))
        methods=[
            name for name in dir(backend)
            if not name.startswith("_") and callable(getattr(backend,name,None))
        ]
        print("[BACKEND] public_methods=",tuple(methods))

    # In-memory instrumentation of the router validator.
    original_validate=getattr(router,"_validate_batch_append_result",None)

    if original_validate is not None:
        def traced_validate(*args,**kwargs):
            print("-"*96)
            print("[TRACE] _validate_batch_append_result invoked")
            print(f"[TRACE] positional_arg_count={len(args)}")
            print(f"[TRACE] keyword_keys={tuple(sorted(kwargs.keys()))}")

            append_result=kwargs.get("append_result")
            if append_result is None:
                # Locate any non-observation result-like positional object.
                for value in args:
                    if hasattr(value,"committed") or hasattr(value,"accepted") or hasattr(value,"records"):
                        append_result=value
                        break

            if append_result is not None:
                print(f"[APPEND RESULT] type={type(append_result).__module__}.{type(append_result).__name__}")
                print(f"[APPEND RESULT] repr={append_result!r}")
                data=getattr(append_result,"__dict__",None)
                if isinstance(data,dict):
                    print(f"[APPEND RESULT] fields={data}")
                for attr in (
                    "committed","accepted","rejected","inserted","duplicate",
                    "duplicate_count","inserted_count","rejected_count",
                    "reason","error","message","chain_head","previous_chain_head",
                    "new_chain_head","records","evidence",
                ):
                    if hasattr(append_result,attr):
                        try:
                            print(f"[APPEND RESULT] {attr}={getattr(append_result,attr)!r}")
                        except Exception:
                            pass
            else:
                print("[APPEND RESULT] Could not identify append_result argument")

            return original_validate(*args,**kwargs)

        setattr(router,"_validate_batch_append_result",traced_validate)
        print("[TRACE] Installed in-memory append-result instrumentation")
    else:
        print("[WARN] Router has no _validate_batch_append_result attribute")

    # Print the relevant local source around the validator for context.
    try:
        source_file=inspect.getsourcefile(type(router))
        if source_file:
            src=Path(source_file)
            print(f"[SOURCE] router_file={src}")
            lines=src.read_text(encoding="utf-8",errors="ignore").splitlines()
            for idx,line in enumerate(lines):
                if "def _validate_batch_append_result" in line:
                    lo=max(0,idx-5); hi=min(len(lines),idx+85)
                    print("[SOURCE] validator_excerpt:")
                    for n in range(lo,hi):
                        print(f"  {n+1:05d}: {lines[n]}")
                    break
    except Exception as exc:
        print(f"[SOURCE] unable_to_read={type(exc).__name__}: {exc}")

    print("-"*96)
    print("[ACTION] Routing exactly ONE canonical snapshot through existing OLA router")

    try:
        evidence=router.route_batch((observation,),now)
        evidence=tuple(evidence)
        print(f"[ROUTE SUCCESS] evidence_count={len(evidence)}")
        for i,item in enumerate(evidence,1):
            print(f"[ROUTE SUCCESS] {i}: {item!r}")
        print("[DIAGNOSIS] Single snapshot persistence succeeded.")
        print("[NEXT] Original 100-record failure is likely batch-size/chain/concurrency related.")
        print("[PASS] No OPC/OLA source files modified")
        return 0

    except Exception as exc:
        print("-"*96)
        print("[ROUTE FAILURE]")
        print(f"[EXCEPTION] type={type(exc).__module__}.{type(exc).__name__}")
        print(f"[EXCEPTION] message={exc}")
        print("[EXCEPTION CHAIN]")
        current=exc
        depth=0
        seen=set()
        while current is not None and id(current) not in seen and depth<10:
            seen.add(id(current))
            print(f"  depth={depth} type={type(current).__name__} message={current}")
            nxt=current.__cause__ if current.__cause__ is not None else current.__context__
            current=nxt
            depth+=1

        print("[TRACEBACK]")
        traceback.print_exc()

        print("-"*96)
        print("[DIAGNOSIS] Persistence failure reproduced with ONE snapshot.")
        print("[NEXT] Use the traced append-result fields above to isolate the exact OLA persistence invariant.")
        print("[PASS] Diagnostic used runtime instrumentation only")
        print("[PASS] Frozen OLR-001 through OLR-045 untouched")
        print("[PASS] Certified OLA source files untouched")
        print("[PASS] execution_authority=FALSE")
        return 1

if __name__=="__main__":
    raise SystemExit(main())

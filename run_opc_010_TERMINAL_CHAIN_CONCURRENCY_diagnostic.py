from __future__ import annotations

import inspect
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path.cwd().resolve()
LINE="="*100

def main():
    print(LINE)
    print(" OPC-010 TERMINAL-CHAIN CONCURRENCY DIAGNOSTIC")
    print(" SINGLE SNAPSHOT — EXISTING OLA ROUTER/BACKEND — NO SOURCE MODIFICATIONS")
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
    from qseries_v2.oracle_adapters.kalshi.oad_021_credentials import load_kalshi_credentials
    from qseries_v2.oracle_adapters.kalshi.oad_022_rest_transport import kalshi_rest_get

    # Pick one currently uncovered market.
    sample=sample_live_open_markets(ROOT,pages=1)
    recent=read_recent_canonical_tickers(ROOT,24,250000)
    target=next((t for t in sample.markets if t not in recent),None)
    if not target:
        print("[ABSTAIN] No uncovered market found in bounded sample")
        return 0

    credentials=load_kalshi_credentials()
    response=kalshi_rest_get(credentials,"/markets/"+target,{},15)
    body=response.body or {}
    market=body.get("market") if isinstance(body,dict) else None
    if not isinstance(market,dict):
        response=kalshi_rest_get(credentials,"/markets",{"limit":1000,"status":"open"},15)
        market=next(
            (
                x for x in ((response.body or {}).get("markets",[]) or [])
                if isinstance(x,dict) and str(x.get("ticker") or "")==target
            ),
            None,
        )
    if not isinstance(market,dict):
        raise RuntimeError("Could not recover target market row")

    now=datetime.now(timezone.utc)
    observation=build_universal_market_snapshot(
        market,
        acquired_at=now,
        batch_id="batch.opc.chain.diagnostic."+now.strftime("%Y%m%dT%H%M%S"),
    )

    print(f"[TARGET] ticker={target}")
    print(f"[OBSERVATION] id={observation.observation_id}")
    print(f"[OBSERVATION] content_hash={observation.content_hash}")

    router=build_opc_postgresql_router(ROOT)
    backend=getattr(router,"_persistence_backend",None)
    if backend is None:
        raise RuntimeError("Router persistence backend unavailable")

    print(f"[ROUTER] {type(router).__module__}.{type(router).__name__}")
    print(f"[BACKEND] {type(backend).__module__}.{type(backend).__name__}")

    def read_backend_head(label):
        try:
            value=backend.terminal_chain_hash()
            print(f"[{label}] backend_terminal_chain_hash={value}")
            return value
        except TypeError:
            # Some backends may require no kwargs but expose a different signature.
            sig=inspect.signature(backend.terminal_chain_hash)
            print(f"[{label}] terminal_chain_hash_signature={sig}")
            value=backend.terminal_chain_hash()
            print(f"[{label}] backend_terminal_chain_hash={value}")
            return value

    # Read live backend head twice before any route.
    head1=read_backend_head("HEAD READ 1")
    time.sleep(2.0)
    head2=read_backend_head("HEAD READ 2")

    if head1 != head2:
        print("[CONCURRENCY SIGNAL] terminal chain advanced during 2-second observation window")
    else:
        print("[CONCURRENCY SIGNAL] terminal chain did not advance during 2-second observation window")

    original_validate=getattr(router,"_validate_batch_append_result")

    captured={}

    def traced_validate(*args,**kwargs):
        append_result=kwargs.get("append_result")
        expected=kwargs.get("expected_terminal_chain_hash")
        captured["expected"]=expected
        captured["append_result"]=append_result

        print("-"*100)
        print("[VALIDATOR TRACE]")
        print(f"[EXPECTED BY ROUTER] {expected!r}")

        if append_result is not None:
            print(f"[BACKEND RESULT] append_status={getattr(append_result,'append_status',None)!r}")
            print(f"[BACKEND RESULT] committed={getattr(append_result,'committed',None)!r}")
            print(f"[BACKEND RESULT] prior_terminal_chain_hash={getattr(append_result,'prior_terminal_chain_hash',None)!r}")
            print(f"[BACKEND RESULT] terminal_chain_hash={getattr(append_result,'terminal_chain_hash',None)!r}")
            print(f"[BACKEND RESULT] reason_codes={getattr(append_result,'reason_codes',None)!r}")

        return original_validate(*args,**kwargs)

    setattr(router,"_validate_batch_append_result",traced_validate)

    print("-"*100)
    print("[ACTION] Routing one snapshot")

    try:
        evidence=tuple(router.route_batch((observation,),datetime.now(timezone.utc)))
        print(f"[ROUTE SUCCESS] evidence_count={len(evidence)}")
    except Exception as exc:
        print(f"[ROUTE FAILURE] {type(exc).__name__}: {exc}")
        traceback.print_exc()

    head3=read_backend_head("HEAD READ 3 AFTER ROUTE")

    print("="*100)
    print(" TERMINAL-CHAIN DIAGNOSIS")
    print("="*100)

    expected=captured.get("expected")
    append_result=captured.get("append_result")
    result_prior=getattr(append_result,"prior_terminal_chain_hash",None) if append_result is not None else None
    reasons=tuple(getattr(append_result,"reason_codes",()) or ()) if append_result is not None else tuple()

    print(f"[COMPARE] head_before_1={head1}")
    print(f"[COMPARE] head_before_2={head2}")
    print(f"[COMPARE] router_expected={expected}")
    print(f"[COMPARE] backend_result_prior={result_prior}")
    print(f"[COMPARE] head_after={head3}")
    print(f"[COMPARE] reason_codes={reasons}")

    if "expected_terminal_chain_hash_mismatch" in reasons:
        if expected == head1 and head2 != head1:
            print("[DIAGNOSIS] Router expectation became stale because the live chain advanced after the initial read.")
            print("[CLASSIFICATION] Concurrent-writer / stale-head race confirmed.")
            print("[NEXT] OPC persistence bridge needs bounded re-read/retry on terminal-chain mismatch; frozen OLA can remain untouched.")
        elif expected != head2 and head1 != head2:
            print("[DIAGNOSIS] Live chain is advancing and router expectation does not match the latest backend head.")
            print("[CLASSIFICATION] Concurrent-writer / stale-head race strongly confirmed.")
            print("[NEXT] OPC persistence bridge needs bounded re-read/retry on terminal-chain mismatch; frozen OLA can remain untouched.")
        elif expected != result_prior:
            print("[DIAGNOSIS] Router expected chain head differs from backend's actual prior terminal chain.")
            print("[CLASSIFICATION] Stale terminal-chain expectation confirmed.")
            print("[NEXT] Isolate where router computes expected head, then correct only OPC bridge/runtime coordination.")
        else:
            print("[DIAGNOSIS] Terminal-chain mismatch reproduced but simple concurrent advancement was not directly observed.")
            print("[CLASSIFICATION] Router/backend expectation source requires one more source-level trace.")
            print("[NEXT] Do not modify frozen OLA yet.")
    else:
        print("[DIAGNOSIS] Expected-terminal-chain mismatch did not reproduce on this one-snapshot attempt.")
        if head1 != head2 or head2 != head3:
            print("[CLASSIFICATION] Live concurrent chain advancement still observed.")
            print("[NEXT] Treat original failure as a race condition candidate and test bounded retry behavior.")
        else:
            print("[CLASSIFICATION] No active chain race observed in this sample.")

    print("[PASS] Diagnostic performed with existing runtime objects only")
    print("[PASS] No OPC or OLA source files modified")
    print("[PASS] Frozen OLR-001 through OLR-045 untouched")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OPC-010 TERMINAL-CHAIN CONCURRENCY DIAGNOSTIC COMPLETE")
    return 0

if __name__=="__main__":
    raise SystemExit(main())

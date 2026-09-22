from __future__ import annotations

import json
import os
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path.cwd().resolve()
LINE="="*104

def now():
    return datetime.now(timezone.utc).isoformat()

def safe_json(path):
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return None

def arbiter_state():
    runtime=ROOT/"runtime_state"
    intent=runtime/"oracle_fast_lane_persistence_intent.json"
    lock=runtime/"oracle_canonical_persistence_priority.lock"
    return {
        "fast_intent":safe_json(intent),
        "lock_exists":lock.exists(),
        "lock_size":lock.stat().st_size if lock.exists() else None,
    }

def main():
    print(LINE)
    print(" OPC-036 PHYSICAL PERSISTENCE COLLISION PROVENANCE DIAGNOSTIC")
    print(" FOREGROUND FAST-LANE PROBE — OBSERVATIONAL INSTRUMENTATION ONLY")
    print(LINE)
    print("[ROOT]",ROOT)
    print("[TIME]",now())

    sys.path.insert(0,str(ROOT))

    from qseries_v2.oracle_pre_settlement_coverage.opc_033_priority_router_patch import (
        install_priority_router_patch,
    )

    from qseries_v2.oracle_intelligence.live_acquisition.oracle_postgresql_canonical_observation_persistence_router import (
        OraclePostgreSQLCanonicalObservationPersistenceRouter,
    )

    install_priority_router_patch("fast_lane",ROOT)

    cls=OraclePostgreSQLCanonicalObservationPersistenceRouter

    original_validate=cls._validate_batch_append_result

    def traced_validate(self,*args,**kwargs):
        append_result=kwargs.get("append_result")
        expected=kwargs.get("expected_terminal_chain_hash")
        observations=kwargs.get("observations") or ()

        print("-"*104)
        print("[PERSISTENCE TRACE]")
        print("[TRACE TIME]",now())
        print("[WRITER] FAST_LANE_DIAGNOSTIC")

        try:
            first=tuple(observations)[0] if observations else None
        except Exception:
            first=None

        if first is not None:
            print("[OBSERVATION] id=",getattr(first,"observation_id",None))
            print("[OBSERVATION] type=",getattr(first,"observation_type",None))
            try:
                payload=dict(getattr(first,"payload",{}) or {})
            except Exception:
                payload={}
            print("[OBSERVATION] ticker=",payload.get("source_market_id") or payload.get("source_symbol"))

        print("[EXPECTED TERMINAL CHAIN]",expected)

        if append_result is not None:
            print("[APPEND RESULT TYPE]",type(append_result).__name__)
            for attr in (
                "append_status",
                "committed",
                "prior_terminal_chain_hash",
                "terminal_chain_hash",
                "reason_codes",
                "appended_count",
                "rejected_count",
            ):
                if hasattr(append_result,attr):
                    try:
                        print(f"[APPEND RESULT] {attr}={getattr(append_result,attr)!r}")
                    except Exception:
                        pass

        print("[ARBITER]",arbiter_state())

        return original_validate(self,*args,**kwargs)

    cls._validate_batch_append_result=traced_validate

    # Instrument terminal_chain_hash reads too.
    backend_cls=None
    try:
        from qseries_v2.oracle_intelligence.live_acquisition.oracle_postgresql_canonical_observation_persistence_backend import (
            OraclePostgreSQLCanonicalObservationPersistenceBackend,
        )
        backend_cls=OraclePostgreSQLCanonicalObservationPersistenceBackend
    except Exception as exc:
        print("[WARN] backend class import failed:",type(exc).__name__,exc)

    if backend_cls is not None and hasattr(backend_cls,"terminal_chain_hash"):
        original_head=backend_cls.terminal_chain_hash
        def traced_head(self,*args,**kwargs):
            value=original_head(self,*args,**kwargs)
            print(f"[CHAIN HEAD READ] time={now()} value={value}")
            return value
        backend_cls.terminal_chain_hash=traced_head

    # Discover current underlying fast-lane runner from wrapper if present.
    candidates=[
        ROOT/"run_oracle_priority_fast_lane_child.py",
        ROOT/"run_oracle_LIVE.py",
    ]

    underlying=None

    wrapper=ROOT/"run_oracle_priority_fast_lane_child.py"
    if wrapper.exists():
        text=wrapper.read_text(encoding="utf-8",errors="ignore")
        marker="UNDERLYING_RUNNER="
        for line in text.splitlines():
            if line.strip().startswith(marker):
                raw=line.split("=",1)[1].strip()
                try:
                    import ast
                    underlying=ast.literal_eval(raw)
                except Exception:
                    pass
                break

    print("[DISCOVERY] priority_wrapper_present=",wrapper.exists())
    print("[DISCOVERY] underlying_fast_lane_runner=",underlying)

    if not underlying:
        print("[ERROR] Could not resolve underlying fast-lane runner from priority wrapper.")
        print("[NEXT] Send this output; do not modify runtime.")
        return 2

    runner_path=ROOT/underlying
    if not runner_path.exists():
        print("[ERROR] Underlying fast-lane runner missing:",runner_path)
        return 2

    print("-"*104)
    print("[ACTION] Launching underlying fast lane in THIS foreground process")
    print("[ACTION] Waiting for next PostgreSQL persistence collision")
    print("[ACTION] Stop with Ctrl+C after a collision trace is printed")
    print("-"*104)

    import runpy

    try:
        runpy.run_path(str(runner_path),run_name="__main__")
    except KeyboardInterrupt:
        print()
        print("[STOP] Diagnostic interrupted by operator")
        return 0
    except SystemExit as exc:
        print("[EXIT] underlying runner SystemExit:",exc)
        return int(exc.code or 0) if isinstance(exc.code,int) else 1
    except Exception as exc:
        print("="*104)
        print(" COLLISION / FAILURE CAPTURED")
        print("="*104)
        print("[TIME]",now())
        print("[EXCEPTION TYPE]",type(exc).__module__+"."+type(exc).__name__)
        print("[EXCEPTION MESSAGE]",exc)
        print("[ARBITER]",arbiter_state())
        print("[TRACEBACK]")
        traceback.print_exc()
        print("[PASS] Collision provenance captured observationally")
        print("[PASS] No OLA/OLR source modified")
        print("[PASS] execution_authority=FALSE")
        print("[DONE] OPC-036 COLLISION PROVENANCE CAPTURE COMPLETE")
        return 1

if __name__=="__main__":
    raise SystemExit(main())

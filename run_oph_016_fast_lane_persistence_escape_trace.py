from __future__ import annotations

import json
import os
import runpy
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path.cwd().resolve()
TRACE=ROOT/"runtime_state"/"oph_016_fast_lane_escape_trace.jsonl"
LINE="="*108

def utcnow():
    return datetime.now(timezone.utc).isoformat()

def emit(kind,**payload):
    record={
        "ts":utcnow(),
        "pid":os.getpid(),
        "kind":str(kind),
        **payload,
    }
    TRACE.parent.mkdir(parents=True,exist_ok=True)
    with TRACE.open("a",encoding="utf-8") as f:
        f.write(json.dumps(record,sort_keys=True,default=str)+"\n")

    if kind in {
        "ROUTER_EXCEPTION",
        "QUEUE_AWAIT_EXCEPTION",
        "FAST_LANE_TOP_EXCEPTION",
        "WRITER_FAILURE_RECORD",
    }:
        print(LINE,flush=True)
        print(f"[OPH-016 ESCAPE TRACE] kind={kind}",flush=True)
        for k,v in record.items():
            print(f"[OPH-016] {k}={v}",flush=True)
        print(LINE,flush=True)

    return record

def safe_payload_ticker(observation):
    try:
        payload=dict(getattr(observation,"payload",{}) or {})
        return (
            payload.get("source_market_id")
            or payload.get("source_symbol")
            or payload.get("ticker")
        )
    except Exception:
        return None

def discover_underlying_fast_lane():
    candidates=[
        ROOT/"run_oph_015_strict_fast_lane_child.py",
        ROOT/"run_oph_010_fast_lane_queue_child.py",
        ROOT/"run_oracle_serialized_fast_lane_child.py",
        ROOT/"run_oracle_priority_fast_lane_child.py",
    ]

    import ast

    for path in candidates:
        if not path.exists():
            continue

        text=path.read_text(encoding="utf-8",errors="ignore")
        for line in text.splitlines():
            if line.strip().startswith("UNDERLYING_RUNNER="):
                try:
                    value=ast.literal_eval(
                        line.split("=",1)[1].strip()
                    )
                    if value:
                        return str(value),path.name
                except Exception:
                    pass

    fallback="run_oad_054_kalshi_global_fast_lane.py"
    if (ROOT/fallback).exists():
        return fallback,"direct_fallback"

    raise RuntimeError(
        "Could not discover physical Fast Lane runner"
    )

def install_trace():
    sys.path.insert(0,str(ROOT))

    from qseries_v2.oracle_intelligence.live_acquisition.oracle_postgresql_canonical_observation_persistence_router import (
        OraclePostgreSQLCanonicalObservationPersistenceRouter,
    )

    cls=OraclePostgreSQLCanonicalObservationPersistenceRouter
    original_route=cls.route_batch

    def traced_route(self,observations,routed_at,*args,**kwargs):
        items=tuple(observations)
        first=items[0] if items else None

        emit(
            "ROUTER_ENTRY",
            observation_count=len(items),
            observation_id=getattr(first,"observation_id",None) if first else None,
            observation_type=getattr(first,"observation_type",None) if first else None,
            ticker=safe_payload_ticker(first) if first else None,
            router_class=type(self).__module__+"."+type(self).__name__,
        )

        try:
            result=original_route(
                self,
                items,
                routed_at,
                *args,
                **kwargs,
            )

            emit(
                "ROUTER_SUCCESS",
                observation_count=len(items),
                result_count=len(tuple(result)),
            )
            return result

        except Exception as exc:
            emit(
                "ROUTER_EXCEPTION",
                observation_count=len(items),
                exception_type=type(exc).__module__+"."+type(exc).__name__,
                exception_message=str(exc),
                traceback="".join(
                    traceback.format_exception(
                        type(exc),
                        exc,
                        exc.__traceback__,
                    )
                ),
            )
            raise

    cls.route_batch=traced_route

    # Trace OPH queue submit / await from the physical module namespace.
    import qseries_v2.oracle_production_hardening.oph_006_durable_cross_process_observation_queue as q

    original_submit=q.submit_observation_batch
    original_await=q.await_request

    def traced_submit(writer_id,priority,observations,root=None):
        items=tuple(observations)

        emit(
            "QUEUE_SUBMIT_ENTRY",
            writer_id=str(writer_id),
            priority=int(priority),
            observation_count=len(items),
        )

        try:
            sub=original_submit(
                writer_id,
                priority,
                items,
                root,
            )

            emit(
                "QUEUE_SUBMIT_SUCCESS",
                writer_id=str(writer_id),
                request_id=sub.request_id,
                priority=int(priority),
                observation_count=len(items),
            )

            return sub

        except Exception as exc:
            emit(
                "QUEUE_SUBMIT_EXCEPTION",
                writer_id=str(writer_id),
                priority=int(priority),
                exception_type=type(exc).__module__+"."+type(exc).__name__,
                exception_message=str(exc),
            )
            raise

    def traced_await(request_id,root=None,timeout_seconds=30.0,poll_seconds=0.005):
        emit(
            "QUEUE_AWAIT_ENTRY",
            request_id=str(request_id),
            timeout_seconds=float(timeout_seconds),
        )

        try:
            result=original_await(
                request_id,
                root,
                timeout_seconds,
                poll_seconds,
            )

            emit(
                "QUEUE_AWAIT_SUCCESS",
                request_id=str(request_id),
                result_count=len(tuple(result)),
            )

            return result

        except Exception as exc:
            emit(
                "QUEUE_AWAIT_EXCEPTION",
                request_id=str(request_id),
                exception_type=type(exc).__module__+"."+type(exc).__name__,
                exception_message=str(exc),
                traceback="".join(
                    traceback.format_exception(
                        type(exc),
                        exc,
                        exc.__traceback__,
                    )
                ),
            )
            raise

    q.submit_observation_batch=traced_submit
    q.await_request=traced_await

    # Patch the OPH strict Fast Lane module globals too, because it imported
    # these functions directly at module import time.
    try:
        import qseries_v2.oracle_production_hardening.oph_012_strict_fast_lane_queue_only_admission as flq
        flq.submit_observation_batch=traced_submit
        flq.await_request=traced_await
        emit("PATCHED_STRICT_FAST_LANE_QUEUE_MODULE")
    except Exception as exc:
        emit(
            "STRICT_FAST_LANE_PATCH_WARNING",
            exception_type=type(exc).__name__,
            exception_message=str(exc),
        )

def tail_recent_failures():
    prov=ROOT/"runtime_state"/"oracle_canonical_persistence_provenance.jsonl"

    if not prov.exists():
        return

    try:
        lines=prov.read_text(
            encoding="utf-8",
            errors="ignore",
        ).splitlines()[-500:]

        for raw in lines:
            try:
                obj=json.loads(raw)
            except Exception:
                continue

            if obj.get("kind") in {
                "WRITER_FAILURE",
                "PRODUCER_FAILURE",
            }:
                emit(
                    "WRITER_FAILURE_RECORD",
                    provenance=obj,
                )

    except Exception as exc:
        emit(
            "PROVENANCE_READ_WARNING",
            exception_type=type(exc).__name__,
            exception_message=str(exc),
        )

def main():
    print(LINE)
    print(" OPH-016 FAST LANE PERSISTENCE ESCAPE TRACE")
    print(" FOREGROUND PHYSICAL FAST LANE — NO PRODUCTION SOURCE MODIFICATIONS")
    print(LINE)

    TRACE.unlink(missing_ok=True)

    runner,discovered_from=discover_underlying_fast_lane()

    print(f"[UNDERLYING FAST LANE] {runner}")
    print(f"[DISCOVERED FROM] {discovered_from}")
    print(f"[TRACE FILE] {TRACE}")
    print("[ACTION] Let it run until the next persistence failure or reconnect.")
    print("[ACTION] Then press Ctrl+C and send the ending trace.")

    emit(
        "TRACE_START",
        underlying_runner=runner,
        discovered_from=discovered_from,
    )

    install_trace()
    tail_recent_failures()

    # Install strict queue-only Fast Lane migration in this same process.
    from qseries_v2.oracle_production_hardening.oph_012_strict_fast_lane_queue_only_admission import (
        install_strict_fast_lane_queue_only,
    )

    install_strict_fast_lane_queue_only(ROOT)

    emit(
        "STRICT_QUEUE_ONLY_ACTIVE",
        direct_postgresql_write_authority=False,
    )

    try:
        runpy.run_path(
            str(ROOT/runner),
            run_name="__main__",
        )

    except KeyboardInterrupt:
        print()
        emit("TRACE_STOPPED_BY_OPERATOR")
        print("[STOP] OPH-016 stopped by operator")
        return 0

    except Exception as exc:
        emit(
            "FAST_LANE_TOP_EXCEPTION",
            exception_type=type(exc).__module__+"."+type(exc).__name__,
            exception_message=str(exc),
            traceback="".join(
                traceback.format_exception(
                    type(exc),
                    exc,
                    exc.__traceback__,
                )
            ),
        )
        return 1

    finally:
        tail_recent_failures()

    return 0

if __name__=="__main__":
    raise SystemExit(main())

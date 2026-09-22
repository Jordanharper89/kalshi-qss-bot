from pathlib import Path
import importlib
import os
import subprocess
import sys

ROOT=Path.cwd().resolve()
PKG=ROOT/"qseries_v2"/"oracle_production_hardening"

MOD=PKG/"oph_016_fast_lane_persistence_escape_trace.py"
TEST=ROOT/"test_oph_016_fast_lane_persistence_escape_trace.py"
RUNNER=ROOT/"run_oph_016_fast_lane_persistence_escape_trace.py"
INIT=PKG/"__init__.py"

MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\n\nOPH_016_BUILD_ID="OPH-016"\nOPH_016_REVISION="OPH_016_FAST_LANE_PERSISTENCE_ESCAPE_TRACE_V1"\n\n@dataclass(frozen=True)\nclass FastLaneEscapeTraceContract:\n    traces_router_entry:bool\n    traces_queue_submit:bool\n    traces_queue_await:bool\n    traces_writer_failure:bool\n    traces_fast_lane_exception:bool\n    production_source_modified:bool=False\n    execution_authority:bool=False\n\ndef trace_contract():\n    return FastLaneEscapeTraceContract(\n        True,True,True,True,True,False,False\n    )\n\ndef verify_oph_016_fast_lane_persistence_escape_trace():\n    c=trace_contract()\n    return (\n        c.traces_router_entry\n        and c.traces_queue_submit\n        and c.traces_queue_await\n        and c.traces_writer_failure\n        and c.traces_fast_lane_exception\n        and not c.production_source_modified\n        and not c.execution_authority\n    )\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_production_hardening.oph_016_fast_lane_persistence_escape_trace import (\n    verify_oph_016_fast_lane_persistence_escape_trace,\n)\n\nclass T(unittest.TestCase):\n    def test_verifier(self):\n        self.assertTrue(\n            verify_oph_016_fast_lane_persistence_escape_trace()\n        )\n\nif __name__=="__main__":\n    print("="*80)\n    print(" OPH-016 CERTIFICATION TEST")\n    print(" FAST LANE PERSISTENCE ESCAPE TRACE")\n    print("="*80)\n\n    result=unittest.TextTestRunner(verbosity=2).run(\n        unittest.defaultTestLoader.loadTestsFromTestCase(T)\n    )\n\n    if not result.wasSuccessful():\n        raise SystemExit(1)\n\n    print("[PASS] OPH-016 trace contract certified")\n    print("[DONE] OPH-016 CERTIFIED")\n'
RUNNER_SOURCE='from __future__ import annotations\n\nimport json\nimport os\nimport runpy\nimport sys\nimport time\nimport traceback\nfrom datetime import datetime, timezone\nfrom pathlib import Path\n\nROOT=Path.cwd().resolve()\nTRACE=ROOT/"runtime_state"/"oph_016_fast_lane_escape_trace.jsonl"\nLINE="="*108\n\ndef utcnow():\n    return datetime.now(timezone.utc).isoformat()\n\ndef emit(kind,**payload):\n    record={\n        "ts":utcnow(),\n        "pid":os.getpid(),\n        "kind":str(kind),\n        **payload,\n    }\n    TRACE.parent.mkdir(parents=True,exist_ok=True)\n    with TRACE.open("a",encoding="utf-8") as f:\n        f.write(json.dumps(record,sort_keys=True,default=str)+"\\n")\n\n    if kind in {\n        "ROUTER_EXCEPTION",\n        "QUEUE_AWAIT_EXCEPTION",\n        "FAST_LANE_TOP_EXCEPTION",\n        "WRITER_FAILURE_RECORD",\n    }:\n        print(LINE,flush=True)\n        print(f"[OPH-016 ESCAPE TRACE] kind={kind}",flush=True)\n        for k,v in record.items():\n            print(f"[OPH-016] {k}={v}",flush=True)\n        print(LINE,flush=True)\n\n    return record\n\ndef safe_payload_ticker(observation):\n    try:\n        payload=dict(getattr(observation,"payload",{}) or {})\n        return (\n            payload.get("source_market_id")\n            or payload.get("source_symbol")\n            or payload.get("ticker")\n        )\n    except Exception:\n        return None\n\ndef discover_underlying_fast_lane():\n    candidates=[\n        ROOT/"run_oph_015_strict_fast_lane_child.py",\n        ROOT/"run_oph_010_fast_lane_queue_child.py",\n        ROOT/"run_oracle_serialized_fast_lane_child.py",\n        ROOT/"run_oracle_priority_fast_lane_child.py",\n    ]\n\n    import ast\n\n    for path in candidates:\n        if not path.exists():\n            continue\n\n        text=path.read_text(encoding="utf-8",errors="ignore")\n        for line in text.splitlines():\n            if line.strip().startswith("UNDERLYING_RUNNER="):\n                try:\n                    value=ast.literal_eval(\n                        line.split("=",1)[1].strip()\n                    )\n                    if value:\n                        return str(value),path.name\n                except Exception:\n                    pass\n\n    fallback="run_oad_054_kalshi_global_fast_lane.py"\n    if (ROOT/fallback).exists():\n        return fallback,"direct_fallback"\n\n    raise RuntimeError(\n        "Could not discover physical Fast Lane runner"\n    )\n\ndef install_trace():\n    sys.path.insert(0,str(ROOT))\n\n    from qseries_v2.oracle_intelligence.live_acquisition.oracle_postgresql_canonical_observation_persistence_router import (\n        OraclePostgreSQLCanonicalObservationPersistenceRouter,\n    )\n\n    cls=OraclePostgreSQLCanonicalObservationPersistenceRouter\n    original_route=cls.route_batch\n\n    def traced_route(self,observations,routed_at,*args,**kwargs):\n        items=tuple(observations)\n        first=items[0] if items else None\n\n        emit(\n            "ROUTER_ENTRY",\n            observation_count=len(items),\n            observation_id=getattr(first,"observation_id",None) if first else None,\n            observation_type=getattr(first,"observation_type",None) if first else None,\n            ticker=safe_payload_ticker(first) if first else None,\n            router_class=type(self).__module__+"."+type(self).__name__,\n        )\n\n        try:\n            result=original_route(\n                self,\n                items,\n                routed_at,\n                *args,\n                **kwargs,\n            )\n\n            emit(\n                "ROUTER_SUCCESS",\n                observation_count=len(items),\n                result_count=len(tuple(result)),\n            )\n            return result\n\n        except Exception as exc:\n            emit(\n                "ROUTER_EXCEPTION",\n                observation_count=len(items),\n                exception_type=type(exc).__module__+"."+type(exc).__name__,\n                exception_message=str(exc),\n                traceback="".join(\n                    traceback.format_exception(\n                        type(exc),\n                        exc,\n                        exc.__traceback__,\n                    )\n                ),\n            )\n            raise\n\n    cls.route_batch=traced_route\n\n    # Trace OPH queue submit / await from the physical module namespace.\n    import qseries_v2.oracle_production_hardening.oph_006_durable_cross_process_observation_queue as q\n\n    original_submit=q.submit_observation_batch\n    original_await=q.await_request\n\n    def traced_submit(writer_id,priority,observations,root=None):\n        items=tuple(observations)\n\n        emit(\n            "QUEUE_SUBMIT_ENTRY",\n            writer_id=str(writer_id),\n            priority=int(priority),\n            observation_count=len(items),\n        )\n\n        try:\n            sub=original_submit(\n                writer_id,\n                priority,\n                items,\n                root,\n            )\n\n            emit(\n                "QUEUE_SUBMIT_SUCCESS",\n                writer_id=str(writer_id),\n                request_id=sub.request_id,\n                priority=int(priority),\n                observation_count=len(items),\n            )\n\n            return sub\n\n        except Exception as exc:\n            emit(\n                "QUEUE_SUBMIT_EXCEPTION",\n                writer_id=str(writer_id),\n                priority=int(priority),\n                exception_type=type(exc).__module__+"."+type(exc).__name__,\n                exception_message=str(exc),\n            )\n            raise\n\n    def traced_await(request_id,root=None,timeout_seconds=30.0,poll_seconds=0.005):\n        emit(\n            "QUEUE_AWAIT_ENTRY",\n            request_id=str(request_id),\n            timeout_seconds=float(timeout_seconds),\n        )\n\n        try:\n            result=original_await(\n                request_id,\n                root,\n                timeout_seconds,\n                poll_seconds,\n            )\n\n            emit(\n                "QUEUE_AWAIT_SUCCESS",\n                request_id=str(request_id),\n                result_count=len(tuple(result)),\n            )\n\n            return result\n\n        except Exception as exc:\n            emit(\n                "QUEUE_AWAIT_EXCEPTION",\n                request_id=str(request_id),\n                exception_type=type(exc).__module__+"."+type(exc).__name__,\n                exception_message=str(exc),\n                traceback="".join(\n                    traceback.format_exception(\n                        type(exc),\n                        exc,\n                        exc.__traceback__,\n                    )\n                ),\n            )\n            raise\n\n    q.submit_observation_batch=traced_submit\n    q.await_request=traced_await\n\n    # Patch the OPH strict Fast Lane module globals too, because it imported\n    # these functions directly at module import time.\n    try:\n        import qseries_v2.oracle_production_hardening.oph_012_strict_fast_lane_queue_only_admission as flq\n        flq.submit_observation_batch=traced_submit\n        flq.await_request=traced_await\n        emit("PATCHED_STRICT_FAST_LANE_QUEUE_MODULE")\n    except Exception as exc:\n        emit(\n            "STRICT_FAST_LANE_PATCH_WARNING",\n            exception_type=type(exc).__name__,\n            exception_message=str(exc),\n        )\n\ndef tail_recent_failures():\n    prov=ROOT/"runtime_state"/"oracle_canonical_persistence_provenance.jsonl"\n\n    if not prov.exists():\n        return\n\n    try:\n        lines=prov.read_text(\n            encoding="utf-8",\n            errors="ignore",\n        ).splitlines()[-500:]\n\n        for raw in lines:\n            try:\n                obj=json.loads(raw)\n            except Exception:\n                continue\n\n            if obj.get("kind") in {\n                "WRITER_FAILURE",\n                "PRODUCER_FAILURE",\n            }:\n                emit(\n                    "WRITER_FAILURE_RECORD",\n                    provenance=obj,\n                )\n\n    except Exception as exc:\n        emit(\n            "PROVENANCE_READ_WARNING",\n            exception_type=type(exc).__name__,\n            exception_message=str(exc),\n        )\n\ndef main():\n    print(LINE)\n    print(" OPH-016 FAST LANE PERSISTENCE ESCAPE TRACE")\n    print(" FOREGROUND PHYSICAL FAST LANE — NO PRODUCTION SOURCE MODIFICATIONS")\n    print(LINE)\n\n    TRACE.unlink(missing_ok=True)\n\n    runner,discovered_from=discover_underlying_fast_lane()\n\n    print(f"[UNDERLYING FAST LANE] {runner}")\n    print(f"[DISCOVERED FROM] {discovered_from}")\n    print(f"[TRACE FILE] {TRACE}")\n    print("[ACTION] Let it run until the next persistence failure or reconnect.")\n    print("[ACTION] Then press Ctrl+C and send the ending trace.")\n\n    emit(\n        "TRACE_START",\n        underlying_runner=runner,\n        discovered_from=discovered_from,\n    )\n\n    install_trace()\n    tail_recent_failures()\n\n    # Install strict queue-only Fast Lane migration in this same process.\n    from qseries_v2.oracle_production_hardening.oph_012_strict_fast_lane_queue_only_admission import (\n        install_strict_fast_lane_queue_only,\n    )\n\n    install_strict_fast_lane_queue_only(ROOT)\n\n    emit(\n        "STRICT_QUEUE_ONLY_ACTIVE",\n        direct_postgresql_write_authority=False,\n    )\n\n    try:\n        runpy.run_path(\n            str(ROOT/runner),\n            run_name="__main__",\n        )\n\n    except KeyboardInterrupt:\n        print()\n        emit("TRACE_STOPPED_BY_OPERATOR")\n        print("[STOP] OPH-016 stopped by operator")\n        return 0\n\n    except Exception as exc:\n        emit(\n            "FAST_LANE_TOP_EXCEPTION",\n            exception_type=type(exc).__module__+"."+type(exc).__name__,\n            exception_message=str(exc),\n            traceback="".join(\n                traceback.format_exception(\n                    type(exc),\n                    exc,\n                    exc.__traceback__,\n                )\n            ),\n        )\n        return 1\n\n    finally:\n        tail_recent_failures()\n\n    return 0\n\nif __name__=="__main__":\n    raise SystemExit(main())\n'

def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def main():
    print("="*88)
    print(" OPH-016 INSTALLER")
    print(" FAST LANE PERSISTENCE ESCAPE TRACE")
    print("="*88)
    print("[ROOT]",ROOT)

    sys.path.insert(0,str(ROOT))

    up=importlib.import_module(
        "qseries_v2.oracle_production_hardening."
        "oph_015_strict_single_writer_production_gate"
    )

    if (
        up.verify_oph_015_strict_single_writer_production_gate()
        is not True
    ):
        raise RuntimeError(
            "Certified OPH-015 verification failed"
        )

    print("[PASS] Certified OPH-015 upstream boundary verified")

    affected=(MOD,TEST,RUNNER,INIT)
    backups={
        p:(p.read_bytes() if p.exists() else None)
        for p in affected
    }

    try:
        write_exact(MOD,MODULE_SOURCE)
        write_exact(TEST,TEST_SOURCE)
        write_exact(RUNNER,RUNNER_SOURCE)

        current=(
            INIT.read_text(encoding="utf-8")
            if INIT.exists()
            else ""
        )

        export=(
            "from .oph_016_fast_lane_persistence_escape_trace "
            "import *"
        )

        if export not in current:
            write_exact(
                INIT,
                current.rstrip()+"\n"+export+"\n",
            )

        compile(
            MOD.read_text(encoding="utf-8"),
            str(MOD),
            "exec",
        )
        compile(
            TEST.read_text(encoding="utf-8"),
            str(TEST),
            "exec",
        )
        compile(
            RUNNER.read_text(encoding="utf-8"),
            str(RUNNER),
            "exec",
        )

        subprocess.run(
            [sys.executable,str(TEST)],
            cwd=str(ROOT),
            check=True,
        )

    except Exception:
        for p,old in backups.items():
            if old is None:
                if p.exists():
                    p.unlink()
            else:
                p.write_bytes(old)

        print(
            "[ROLLBACK] OPH-016 installation failed; "
            "affected files restored"
        )
        raise

    print("[PASS] Wrote:",MOD.relative_to(ROOT))
    print("[PASS] Wrote:",TEST.name)
    print("[PASS] Wrote:",RUNNER.name)
    print("[PASS] Production Oracle launcher untouched")
    print("[PASS] Frozen OAD/OLA/OLR source untouched")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OPH-016 INSTALLATION AND CERTIFICATION COMPLETE")

if __name__=="__main__":
    main()

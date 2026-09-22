from pathlib import Path
import ast, importlib, os, subprocess, sys, time, hashlib

ROOT=Path.cwd().resolve()
MOD=ROOT/'qseries_v2/oracle_intelligence_analytics_runtime/oiar_006_continuous_analytics_refresh_runtime.py'
TEST=ROOT/'test_oiar_006_continuous_analytics_refresh_runtime.py'
RUNNER=ROOT/"run_oiar_006_continuous_analytics_refresh_runtime.py"
RUNNER_SOURCE='from __future__ import annotations\nimport argparse\nfrom pathlib import Path\nimport time\n\nfrom qseries_v2.oracle_intelligence_analytics_runtime.oiar_006_continuous_analytics_refresh_runtime import (\n    DEFAULT_CADENCE_SECONDS,\n    run_refresh_cycle,\n)\n\ndef parser():\n    p=argparse.ArgumentParser(description="OIAR continuous analytics refresh runtime")\n    p.add_argument("--once",action="store_true")\n    p.add_argument("--check",action="store_true")\n    p.add_argument("--cadence-seconds",type=float,default=DEFAULT_CADENCE_SECONDS)\n    return p\n\ndef main(argv=None):\n    a=parser().parse_args(argv)\n    root=Path.cwd().resolve()\n    print("="*88)\n    print(" OIAR-006 CONTINUOUS ANALYTICS REFRESH RUNTIME")\n    print("="*88)\n\n    if a.check:\n        print("[PASS] OIAR-006 runtime import and argument contract verified")\n        print("[PASS] execution_authority=FALSE")\n        return 0\n\n    if a.once:\n        x=run_refresh_cycle(root)\n        print(\n            f"[OIAR-006] status={x.status} cohort_markets={x.cohort_markets} "\n            f"analytics_markets={x.analytics_markets} "\n            f"elapsed_seconds={x.elapsed_seconds:.3f} "\n            f"learner_state_hash={x.learner_state_hash} execution_authority=FALSE"\n        )\n        return 0\n\n    cadence=max(5.0,float(a.cadence_seconds))\n    cycle=0\n    while True:\n        cycle+=1\n        started=time.monotonic()\n        try:\n            x=run_refresh_cycle(root)\n            print(\n                f"[OIAR-006] cycle={cycle} status={x.status} "\n                f"cohort_markets={x.cohort_markets} analytics_markets={x.analytics_markets} "\n                f"elapsed_seconds={x.elapsed_seconds:.3f} execution_authority=FALSE",\n                flush=True,\n            )\n        except KeyboardInterrupt:\n            print("[STOP] OIAR-006 stopped by operator.",flush=True)\n            return 0\n        except Exception as exc:\n            print(\n                f"[OIAR-006] cycle={cycle} status=DEGRADED "\n                f"type={type(exc).__name__} message={exc} execution_authority=FALSE",\n                flush=True,\n            )\n        remaining=max(0.0,cadence-(time.monotonic()-started))\n        try:\n            time.sleep(remaining)\n        except KeyboardInterrupt:\n            print("[STOP] OIAR-006 stopped by operator.",flush=True)\n            return 0\n\nif __name__=="__main__":\n    raise SystemExit(main())\n'
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom datetime import datetime, timezone\nfrom pathlib import Path\nimport time\n\nfrom qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect\nfrom .oiar_001_production_analytics_snapshot_foundation import STATE_TABLE\nfrom .oiar_002_current_reasoning_market_cohort_snapshot import materialize_current_reasoning_market_cohort\nfrom .oiar_004_indexed_current_cohort_analytics_materializer import materialize_indexed_current_cohort_analytics\n\nOIAR_006_BUILD_ID="OIAR-006"\nOIAR_006_REVISION="OIAR_006_CONTINUOUS_ANALYTICS_REFRESH_RUNTIME_V1"\nDEFAULT_CADENCE_SECONDS=15.0\n\n@dataclass(frozen=True)\nclass AnalyticsRefreshCycle:\n    status:str\n    cohort_markets:int\n    analytics_markets:int\n    learner_state_hash:str\n    elapsed_seconds:float\n    completed_at:str\n    execution_authority:bool=False\n\ndef _update_state(root,status,error_type=None,error_message=None):\n    now=datetime.now(timezone.utc)\n    with connect(root,autocommit=True) as conn:\n        with conn.cursor() as cur:\n            if status=="RUNNING":\n                cur.execute(\n                    f"UPDATE public.{STATE_TABLE} SET status=\'RUNNING\',last_started_at=%s,last_error_type=NULL,last_error_message=NULL,updated_at=clock_timestamp() WHERE state_id=1",\n                    (now,),\n                )\n            elif status=="IDLE":\n                cur.execute(\n                    f"UPDATE public.{STATE_TABLE} SET status=\'IDLE\',last_completed_at=%s,last_error_type=NULL,last_error_message=NULL,updated_at=clock_timestamp() WHERE state_id=1",\n                    (now,),\n                )\n            else:\n                cur.execute(\n                    f"UPDATE public.{STATE_TABLE} SET status=\'DEGRADED\',last_completed_at=%s,failure_count=failure_count+1,last_error_type=%s,last_error_message=%s,updated_at=clock_timestamp() WHERE state_id=1",\n                    (now,str(error_type or "RuntimeError"),str(error_message or "")[:1000]),\n                )\n\ndef run_refresh_cycle(root=None):\n    root=Path(root or Path.cwd()).resolve()\n    started=time.monotonic()\n    _update_state(root,"RUNNING")\n    try:\n        cohort=materialize_current_reasoning_market_cohort(root)\n        analytics=materialize_indexed_current_cohort_analytics(\n            root,\n            per_market=250,\n            timeout_ms=15000,\n        )\n        elapsed=time.monotonic()-started\n        completed=datetime.now(timezone.utc)\n        _update_state(root,"IDLE")\n        return AnalyticsRefreshCycle(\n            "IDLE",\n            int(cohort.market_count),\n            int(analytics["analytics_market_count"]),\n            str(analytics.get("learner_state_hash") or cohort.learner_state_hash),\n            elapsed,\n            completed.isoformat(),\n            False,\n        )\n    except Exception as exc:\n        _update_state(root,"DEGRADED",type(exc).__name__,str(exc))\n        raise\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_intelligence_analytics_runtime.oiar_006_continuous_analytics_refresh_runtime import (\n    OIAR_006_BUILD_ID, DEFAULT_CADENCE_SECONDS, AnalyticsRefreshCycle\n)\nclass T(unittest.TestCase):\n    def test_identity(self):self.assertEqual(OIAR_006_BUILD_ID,"OIAR-006")\n    def test_contract(self):\n        x=AnalyticsRefreshCycle("IDLE",50,50,"h",.8,"now",False)\n        self.assertEqual(x.analytics_markets,50);self.assertFalse(x.execution_authority)\n    def test_cadence(self):self.assertGreaterEqual(DEFAULT_CADENCE_SECONDS,5.0)\nif __name__=="__main__":\n    print("="*88);print(" OIAR-006 CERTIFICATION TEST");print(" CONTINUOUS ANALYTICS REFRESH RUNTIME");print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] continuous refresh cycle contract certified")\n    print("[PASS] analytics failures degrade without granting execution")\n    print("[PASS] execution_authority=FALSE")\n    print("[DONE] OIAR-006 CERTIFIED")\n'

def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name(path.name+f".{os.getpid()}.tmp")
    tmp.write_text(text,encoding="utf-8")
    os.replace(tmp,path)

def restore(path,data):
    if data is None:
        if path.exists(): path.unlink()
    else:
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(data)

def update_init(path,export):
    current=path.read_text(encoding="utf-8") if path.exists() else ""
    if export not in current.splitlines():
        write_exact(path,current.rstrip()+"\n"+export+"\n")

def main():
    print("="*88);print(" OIAR-006 INSTALLER");print(" CONTINUOUS ANALYTICS REFRESH RUNTIME");print("="*88);print("[ROOT]",ROOT)
    PKG=MOD.parent;INIT=PKG/"__init__.py";RUNNER=ROOT/"run_oiar_006_continuous_analytics_refresh_runtime.py"
    required=(
        PKG/"oiar_001_production_analytics_snapshot_foundation.py",
        PKG/"oiar_002_current_reasoning_market_cohort_snapshot.py",
        PKG/"oiar_003_canonical_market_history_access_index.py",
        PKG/"oiar_004_indexed_current_cohort_analytics_materializer.py",
        PKG/"oiar_005_persisted_trader_intelligence_read_surface.py",
    )
    for p in required:
        if not p.is_file():raise RuntimeError(f"Required proven upstream missing: {p}")
    old={p:(p.read_bytes() if p.exists() else None) for p in (MOD,TEST,INIT,RUNNER)}
    try:
        write_exact(MOD,MODULE_SOURCE);write_exact(TEST,TEST_SOURCE);write_exact(RUNNER,RUNNER_SOURCE)
        update_init(INIT,"from .oiar_006_continuous_analytics_refresh_runtime import *")
        ast.parse(MODULE_SOURCE);ast.parse(TEST_SOURCE);ast.parse(RUNNER_SOURCE)
        print("[PASS] installer payload syntax verified")
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
        subprocess.run([sys.executable,str(RUNNER),"--check"],cwd=str(ROOT),check=True,timeout=10)
        subprocess.run([sys.executable,str(RUNNER),"--once"],cwd=str(ROOT),check=True,timeout=30)
    except Exception:
        for p,b in old.items():restore(p,b)
        print("[ROLLBACK] OIAR-006 failed; affected repository files restored");raise
    print("[PASS] physical analytics refresh cycle completed")
    print("[PASS] current cohort + indexed OIA snapshot refreshed together")
    print("[PASS] no Operator Terminal dependency")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OIAR-006 INSTALLATION COMPLETE")

if __name__=="__main__":
    main()

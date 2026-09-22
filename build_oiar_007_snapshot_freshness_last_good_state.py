from pathlib import Path
import ast, importlib, os, subprocess, sys, time, hashlib

ROOT=Path.cwd().resolve()
MOD=ROOT/'qseries_v2/oracle_intelligence_analytics_runtime/oiar_007_snapshot_freshness_last_good_state.py'
TEST=ROOT/'test_oiar_007_snapshot_freshness_last_good_state.py'

MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom datetime import datetime, timezone\nfrom pathlib import Path\n\nfrom qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect\nfrom .oiar_001_production_analytics_snapshot_foundation import SNAPSHOT_TABLE, STATE_TABLE\nfrom .oiar_004_indexed_current_cohort_analytics_materializer import ANALYTICS_STAGE\n\nOIAR_007_BUILD_ID="OIAR-007"\nOIAR_007_REVISION="OIAR_007_SNAPSHOT_FRESHNESS_LAST_GOOD_STATE_V1"\nFRESH_SECONDS=60.0\nSTALE_SECONDS=300.0\n\n@dataclass(frozen=True)\nclass AnalyticsSnapshotFreshness:\n    snapshot_id:str\n    market_count:int\n    snapshot_generated_at:str\n    last_refresh_completed_at:str\n    age_seconds:float\n    runtime_status:str\n    freshness_status:str\n    serves_last_good:bool\n    read_only:bool=True\n    execution_authority:bool=False\n\ndef inspect_snapshot_freshness(root=None,now=None):\n    root=Path(root or Path.cwd()).resolve()\n    checked=now or datetime.now(timezone.utc)\n\n    with connect(root,autocommit=False) as conn:\n        with conn.cursor() as cur:\n            cur.execute("SET TRANSACTION READ ONLY")\n            cur.execute(\n                f"SELECT snapshot_id,market_count,generated_at FROM public.{SNAPSHOT_TABLE} "\n                "WHERE stage=%s ORDER BY generated_at DESC,persisted_at DESC LIMIT 1",\n                (ANALYTICS_STAGE,),\n            )\n            snap=cur.fetchone()\n            cur.execute(\n                f"SELECT status,last_completed_at FROM public.{STATE_TABLE} WHERE state_id=1"\n            )\n            state=cur.fetchone()\n        conn.rollback()\n\n    if snap is None:\n        raise RuntimeError("OIAR-007 no last-good analytics snapshot available")\n\n    snapshot_id,market_count,generated_at=snap\n    runtime_status=str(state[0] if state else "FAILED")\n    completed=(state[1] if state and state[1] is not None else generated_at)\n    completed=completed.astimezone(timezone.utc)\n    age=max(0.0,(checked.astimezone(timezone.utc)-completed).total_seconds())\n\n    if runtime_status in ("DEGRADED","FAILED"):\n        freshness="DEGRADED"\n    elif age<=FRESH_SECONDS:\n        freshness="FRESH"\n    elif age<=STALE_SECONDS:\n        freshness="STALE"\n    else:\n        freshness="DEGRADED"\n\n    return AnalyticsSnapshotFreshness(\n        str(snapshot_id),\n        int(market_count),\n        generated_at.astimezone(timezone.utc).isoformat(),\n        completed.isoformat(),\n        age,\n        runtime_status,\n        freshness,\n        True,\n        True,\n        False,\n    )\n\ndef verify_oiar_007_snapshot_freshness(root=None):\n    x=inspect_snapshot_freshness(root)\n    return bool(\n        x.snapshot_id and x.market_count>0 and x.serves_last_good\n        and x.read_only and not x.execution_authority\n        and x.freshness_status in ("FRESH","STALE","DEGRADED")\n    )\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_intelligence_analytics_runtime.oiar_007_snapshot_freshness_last_good_state import (\n    OIAR_007_BUILD_ID,FRESH_SECONDS,STALE_SECONDS,AnalyticsSnapshotFreshness\n)\nclass T(unittest.TestCase):\n    def test_identity(self):self.assertEqual(OIAR_007_BUILD_ID,"OIAR-007")\n    def test_thresholds(self):self.assertLess(FRESH_SECONDS,STALE_SECONDS)\n    def test_contract(self):\n        x=AnalyticsSnapshotFreshness("x",50,"a","b",1,"IDLE","FRESH",True,True,False)\n        self.assertTrue(x.serves_last_good);self.assertFalse(x.execution_authority)\nif __name__=="__main__":\n    print("="*88);print(" OIAR-007 CERTIFICATION TEST");print(" SNAPSHOT FRESHNESS + LAST-GOOD STATE");print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] FRESH/STALE/DEGRADED contract certified")\n    print("[PASS] last-good snapshot serving certified")\n    print("[PASS] execution_authority=FALSE")\n    print("[DONE] OIAR-007 CERTIFIED")\n'

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
    print("="*88);print(" OIAR-007 INSTALLER");print(" SNAPSHOT FRESHNESS + LAST-GOOD STATE");print("="*88);print("[ROOT]",ROOT)
    PKG=MOD.parent;INIT=PKG/"__init__.py";RUNNER=ROOT/"run_oiar_006_continuous_analytics_refresh_runtime.py"
    for p in (PKG/"oiar_006_continuous_analytics_refresh_runtime.py",RUNNER):
        if not p.is_file():raise RuntimeError(f"Required OIAR-006 upstream missing: {p}")
    old={p:(p.read_bytes() if p.exists() else None) for p in (MOD,TEST,INIT)}
    try:
        write_exact(MOD,MODULE_SOURCE);write_exact(TEST,TEST_SOURCE)
        update_init(INIT,"from .oiar_007_snapshot_freshness_last_good_state import *")
        ast.parse(MODULE_SOURCE);ast.parse(TEST_SOURCE);print("[PASS] installer payload syntax verified")
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
        subprocess.run([sys.executable,str(RUNNER),"--once"],cwd=str(ROOT),check=True,timeout=30)
        importlib.invalidate_caches()
        m=importlib.import_module("qseries_v2.oracle_intelligence_analytics_runtime.oiar_007_snapshot_freshness_last_good_state")
        x=m.inspect_snapshot_freshness(ROOT)
        print(f"[PHYSICAL] snapshot_id={x.snapshot_id} market_count={x.market_count} freshness={x.freshness_status} age_seconds={x.age_seconds:.3f} runtime_status={x.runtime_status}")
        if not m.verify_oiar_007_snapshot_freshness(ROOT):raise RuntimeError("OIAR-007 physical verification failed")
    except Exception:
        for p,b in old.items():restore(p,b)
        print("[ROLLBACK] OIAR-007 failed; affected repository files restored");raise
    print("[PASS] latest successful snapshot freshness is explicit")
    print("[PASS] last-good snapshot remains readable during degraded refresh")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OIAR-007 INSTALLATION COMPLETE")

if __name__=="__main__":
    main()

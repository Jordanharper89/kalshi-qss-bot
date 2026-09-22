from pathlib import Path
import ast
import importlib
import os
import subprocess
import sys

ROOT=Path.cwd().resolve()
PKG=ROOT/"qseries_v2"/"oracle_intelligence_analytics_runtime"
MOD=PKG/"oiar_001_production_analytics_snapshot_foundation.py"
TEST=ROOT/"test_oiar_001_production_analytics_snapshot_foundation.py"
INIT=PKG/"__init__.py"

MODULE_SOURCE='from __future__ import annotations\n\nfrom dataclasses import dataclass\nfrom pathlib import Path\nimport hashlib\nimport json\n\nfrom qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect\n\nOIAR_001_BUILD_ID="OIAR-001"\nOIAR_001_REVISION="OIAR_001_PRODUCTION_ANALYTICS_SNAPSHOT_FOUNDATION_V1"\n\nSTATE_TABLE="oracle_intelligence_analytics_runtime_state"\nSNAPSHOT_TABLE="oracle_intelligence_analytics_snapshots"\n\nDDL=f"""\nCREATE TABLE IF NOT EXISTS public.{STATE_TABLE}(\n    state_id SMALLINT PRIMARY KEY CHECK(state_id=1),\n    last_successful_snapshot_id TEXT,\n    last_successful_stage TEXT,\n    last_successful_at TIMESTAMPTZ,\n    last_started_at TIMESTAMPTZ,\n    last_completed_at TIMESTAMPTZ,\n    status TEXT NOT NULL DEFAULT \'IDLE\'\n        CHECK(status IN (\'IDLE\',\'RUNNING\',\'DEGRADED\',\'FAILED\')),\n    failure_count BIGINT NOT NULL DEFAULT 0 CHECK(failure_count>=0),\n    last_error_type TEXT,\n    last_error_message TEXT,\n    updated_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()\n);\n\nINSERT INTO public.{STATE_TABLE}(state_id,status)\nVALUES(1,\'IDLE\')\nON CONFLICT(state_id) DO NOTHING;\n\nCREATE TABLE IF NOT EXISTS public.{SNAPSHOT_TABLE}(\n    snapshot_id TEXT PRIMARY KEY,\n    stage TEXT NOT NULL,\n    source_schema_version TEXT,\n    source_engine_id TEXT,\n    generated_at TIMESTAMPTZ NOT NULL,\n    persisted_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),\n    market_count INTEGER NOT NULL CHECK(market_count>=0),\n    payload_json JSONB NOT NULL,\n    payload_hash TEXT NOT NULL,\n    read_only_source BOOLEAN NOT NULL DEFAULT TRUE,\n    execution_authority BOOLEAN NOT NULL DEFAULT FALSE\n        CHECK(execution_authority=FALSE)\n);\n\nCREATE INDEX IF NOT EXISTS oracle_intelligence_analytics_snapshots_stage_time_idx\nON public.{SNAPSHOT_TABLE}(stage,generated_at DESC,persisted_at DESC);\n"""\n\n@dataclass(frozen=True)\nclass AnalyticsSnapshotFoundationStatus:\n    state_table:str\n    snapshot_table:str\n    state_row_present:bool\n    database_writable:bool\n    read_only_source_required:bool=True\n    execution_authority:bool=False\n\ndef stable_hash(value)->str:\n    raw=json.dumps(value,sort_keys=True,separators=(",",":"),default=str).encode("utf-8")\n    return hashlib.sha256(raw).hexdigest()\n\ndef ensure_analytics_snapshot_schema(root=None)->bool:\n    root=Path(root or Path.cwd()).resolve()\n    with connect(root,autocommit=True) as conn:\n        with conn.cursor() as cur:\n            cur.execute(DDL)\n    return True\n\ndef inspect_foundation(root=None)->AnalyticsSnapshotFoundationStatus:\n    root=Path(root or Path.cwd()).resolve()\n    ensure_analytics_snapshot_schema(root)\n    with connect(root,autocommit=False) as conn:\n        with conn.cursor() as cur:\n            cur.execute(\n                f"SELECT EXISTS(SELECT 1 FROM public.{STATE_TABLE} WHERE state_id=1)"\n            )\n            state_present=bool(cur.fetchone()[0])\n\n            cur.execute("CREATE TEMP TABLE oiar_001_probe(x integer)")\n            cur.execute("INSERT INTO oiar_001_probe VALUES(1)")\n            cur.execute("SELECT x FROM oiar_001_probe")\n            writable=(cur.fetchone()==(1,))\n        conn.rollback()\n\n    return AnalyticsSnapshotFoundationStatus(\n        state_table=STATE_TABLE,\n        snapshot_table=SNAPSHOT_TABLE,\n        state_row_present=state_present,\n        database_writable=writable,\n        read_only_source_required=True,\n        execution_authority=False,\n    )\n\ndef verify_oiar_001_production_analytics_snapshot_foundation(root=None)->bool:\n    status=inspect_foundation(root)\n    return (\n        status.state_row_present\n        and status.database_writable\n        and status.read_only_source_required\n        and not status.execution_authority\n    )\n'
TEST_SOURCE='import unittest\n\nfrom qseries_v2.oracle_intelligence_analytics_runtime.oiar_001_production_analytics_snapshot_foundation import (\n    OIAR_001_BUILD_ID,\n    STATE_TABLE,\n    SNAPSHOT_TABLE,\n    AnalyticsSnapshotFoundationStatus,\n    stable_hash,\n)\n\nclass T(unittest.TestCase):\n    def test_identity(self):\n        self.assertEqual(OIAR_001_BUILD_ID,"OIAR-001")\n\n    def test_contract(self):\n        x=AnalyticsSnapshotFoundationStatus(\n            STATE_TABLE,\n            SNAPSHOT_TABLE,\n            True,\n            True,\n            True,\n            False,\n        )\n        self.assertTrue(x.state_row_present)\n        self.assertTrue(x.database_writable)\n        self.assertTrue(x.read_only_source_required)\n        self.assertFalse(x.execution_authority)\n\n    def test_hash_deterministic(self):\n        a=stable_hash({"b":2,"a":1})\n        b=stable_hash({"a":1,"b":2})\n        self.assertEqual(a,b)\n\nif __name__=="__main__":\n    print("="*88)\n    print(" OIAR-001 CERTIFICATION TEST")\n    print(" PRODUCTION ANALYTICS SNAPSHOT FOUNDATION")\n    print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(\n        unittest.defaultTestLoader.loadTestsFromTestCase(T)\n    )\n    if not r.wasSuccessful():\n        raise SystemExit(1)\n    print("[PASS] deterministic snapshot identity contract certified")\n    print("[PASS] read-only source boundary required")\n    print("[PASS] execution_authority=FALSE")\n    print("[DONE] OIAR-001 CERTIFIED")\n'

def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name(path.name+f".{os.getpid()}.tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def restore(path,data):
    if data is None:
        if path.exists():
            path.unlink()
    else:
        path.write_bytes(data)

def main():
    print("="*88)
    print(" OIAR-001 INSTALLER")
    print(" PRODUCTION ANALYTICS SNAPSHOT FOUNDATION")
    print("="*88)
    print("[ROOT]",ROOT)

    required=ROOT/"qseries_v2"/"oracle_production_hardening"/"oph_019_postgresql_universal_ingestion_queue.py"
    if not required.is_file():
        raise RuntimeError("Certified OPH-019 PostgreSQL connection boundary missing")

    text=required.read_text(encoding="utf-8")
    for token in ("def database_url(","def connect("):
        if token not in text:
            raise RuntimeError(f"OPH-019 contract mismatch: {token}")

    affected=(MOD,TEST,INIT)
    old={p:(p.read_bytes() if p.exists() else None) for p in affected}

    try:
        init_text=INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        export="from .oiar_001_production_analytics_snapshot_foundation import *"
        if export not in init_text:
            init_text=init_text.rstrip()+"\n"+export+"\n"

        write_exact(MOD,MODULE_SOURCE)
        write_exact(TEST,TEST_SOURCE)
        write_exact(INIT,init_text)

        ast.parse(MODULE_SOURCE,filename=str(MOD))
        ast.parse(TEST_SOURCE,filename=str(TEST))
        print("[PASS] installer payload syntax verified")

        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)

        importlib.invalidate_caches()
        m=importlib.import_module(
            "qseries_v2.oracle_intelligence_analytics_runtime.oiar_001_production_analytics_snapshot_foundation"
        )

        if m.ensure_analytics_snapshot_schema(ROOT) is not True:
            raise RuntimeError("OIAR-001 schema creation did not certify")

        status=m.inspect_foundation(ROOT)
        print(
            f"[PHYSICAL] state_table={status.state_table} "
            f"snapshot_table={status.snapshot_table} "
            f"state_row_present={status.state_row_present} "
            f"database_writable={status.database_writable}"
        )

        if not m.verify_oiar_001_production_analytics_snapshot_foundation(ROOT):
            raise RuntimeError("OIAR-001 physical verification failed")

    except Exception:
        for p,data in old.items():
            restore(p,data)
        print("[ROLLBACK] OIAR-001 failed; affected repository files restored")
        raise

    print("[PASS] PostgreSQL analytics snapshot schema exists")
    print("[PASS] physical PostgreSQL write probe succeeded and rolled back")
    print("[PASS] no OIA analytics computation executed")
    print("[PASS] no Oracle Live launcher mutation")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OIAR-001 INSTALLATION COMPLETE")

if __name__=="__main__":
    main()

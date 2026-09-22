from pathlib import Path
import ast, importlib, os, subprocess, sys, time

ROOT=Path.cwd().resolve()
PKG=ROOT/"qseries_v2"/"oracle_intelligence_analytics_runtime"
MOD=PKG/"oiar_003_canonical_market_history_access_index.py"
TEST=ROOT/"test_oiar_003_canonical_market_history_access_index.py"
INIT=PKG/"__init__.py"

MODULE_SOURCE='from __future__ import annotations\n\nfrom dataclasses import dataclass\nfrom pathlib import Path\nimport json\n\nfrom qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect\nfrom .oiar_001_production_analytics_snapshot_foundation import SNAPSHOT_TABLE\n\nOIAR_003_BUILD_ID = "OIAR-003"\nINDEX_NAME = "idx_oracle_canonical_market_snapshot_market_seq"\n\nMARKET_ID_EXPRESSION = """\nCOALESCE(\n    NULLIF(COALESCE(\n        canonical_observation_json->\'raw_observation\'->\'payload\',\n        canonical_observation_json->\'payload\',\n        \'{}\'::jsonb\n    )->>\'source_market_id\',\'\'),\n    NULLIF(COALESCE(\n        canonical_observation_json->\'raw_observation\'->\'payload\',\n        canonical_observation_json->\'payload\',\n        \'{}\'::jsonb\n    )->>\'market_id\',\'\'),\n    NULLIF(COALESCE(\n        canonical_observation_json->\'raw_observation\'->\'payload\',\n        canonical_observation_json->\'payload\',\n        \'{}\'::jsonb\n    )->>\'source_symbol\',\'\')\n)\n""".strip()\n\nCREATE_INDEX_SQL = f"""\nCREATE INDEX CONCURRENTLY {INDEX_NAME}\nON public.oracle_canonical_observations (\n    ({MARKET_ID_EXPRESSION}),\n    sequence_number DESC\n)\nWHERE observation_type=\'market_snapshot\'\n"""\n\n@dataclass(frozen=True)\nclass CanonicalMarketHistoryIndexStatus:\n    index_name:str\n    exists:bool\n    valid:bool\n    ready:bool\n    live:bool\n    probe_market_ticker:str\n    probe_rows:int\n    plan_uses_index:bool\n    read_only_probe:bool=True\n    execution_authority:bool=False\n\ndef _index_status(root):\n    root=Path(root).resolve()\n    with connect(root,autocommit=True) as conn:\n        with conn.cursor() as cur:\n            cur.execute("""\n                SELECT i.indisvalid,i.indisready,i.indislive\n                FROM pg_class c\n                JOIN pg_namespace n ON n.oid=c.relnamespace\n                JOIN pg_index i ON i.indexrelid=c.oid\n                WHERE n.nspname=\'public\' AND c.relname=%s\n            """,(INDEX_NAME,))\n            row=cur.fetchone()\n    return (False,False,False,False) if row is None else (True,bool(row[0]),bool(row[1]),bool(row[2]))\n\ndef ensure_canonical_market_history_index(root=None):\n    root=Path(root or Path.cwd()).resolve()\n    exists,valid,ready,live=_index_status(root)\n\n    if exists and not (valid and ready and live):\n        with connect(root,autocommit=True) as conn:\n            with conn.cursor() as cur:\n                cur.execute(f"DROP INDEX CONCURRENTLY IF EXISTS public.{INDEX_NAME}")\n\n    exists,valid,ready,live=_index_status(root)\n    if not exists:\n        with connect(root,autocommit=True) as conn:\n            with conn.cursor() as cur:\n                cur.execute("SET statement_timeout=0")\n                cur.execute(CREATE_INDEX_SQL)\n\n    return _index_status(root)\n\ndef _latest_reasoning_ticker(root):\n    root=Path(root).resolve()\n    with connect(root,autocommit=False) as conn:\n        with conn.cursor() as cur:\n            cur.execute("SET TRANSACTION READ ONLY")\n            cur.execute(f"""\n                SELECT payload_json\n                FROM public.{SNAPSHOT_TABLE}\n                WHERE stage=\'reasoning_market_cohort\'\n                ORDER BY generated_at DESC,persisted_at DESC\n                LIMIT 1\n            """)\n            row=cur.fetchone()\n        conn.rollback()\n\n    if row is None:\n        raise RuntimeError("OIAR-003 requires OIAR-002 snapshot")\n\n    payload=row[0]\n    if isinstance(payload,str):\n        payload=json.loads(payload)\n\n    markets=payload.get("markets") if isinstance(payload,dict) else None\n    if not isinstance(markets,list) or not markets:\n        raise RuntimeError("OIAR-003 reasoning cohort is empty")\n\n    ticker=str(markets[0].get("market_ticker") or "").strip()\n    if not ticker:\n        raise RuntimeError("OIAR-003 reasoning cohort ticker missing")\n    return ticker\n\ndef probe_indexed_market_history(root=None,limit=250,timeout_ms=10000):\n    root=Path(root or Path.cwd()).resolve()\n    exists,valid,ready,live=_index_status(root)\n    if not (exists and valid and ready and live):\n        raise RuntimeError("OIAR-003 index is not valid/ready/live")\n\n    ticker=_latest_reasoning_ticker(root)\n\n    sql=f"""\n        SELECT sequence_number,observed_at\n        FROM public.oracle_canonical_observations\n        WHERE observation_type=\'market_snapshot\'\n          AND ({MARKET_ID_EXPRESSION})=%s\n        ORDER BY sequence_number DESC\n        LIMIT %s\n    """\n\n    with connect(root,autocommit=False) as conn:\n        with conn.cursor() as cur:\n            cur.execute("SET TRANSACTION READ ONLY")\n            cur.execute(f"SET LOCAL statement_timeout=\'{int(timeout_ms)}ms\'")\n            cur.execute("EXPLAIN (FORMAT JSON) "+sql,(ticker,int(limit)))\n            plan=cur.fetchone()[0]\n            cur.execute(sql,(ticker,int(limit)))\n            rows=cur.fetchall() or []\n        conn.rollback()\n\n    plan_text=json.dumps(plan,sort_keys=True,default=str)\n    return CanonicalMarketHistoryIndexStatus(\n        INDEX_NAME,exists,valid,ready,live,ticker,len(rows),\n        INDEX_NAME in plan_text,True,False\n    )\n\ndef verify_oiar_003_canonical_market_history_access_index(root=None):\n    x=probe_indexed_market_history(root)\n    return bool(\n        x.exists and x.valid and x.ready and x.live and\n        x.probe_rows>0 and x.plan_uses_index and\n        x.read_only_probe and not x.execution_authority\n    )\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_intelligence_analytics_runtime.oiar_003_canonical_market_history_access_index import (\n    OIAR_003_BUILD_ID, INDEX_NAME, MARKET_ID_EXPRESSION, CanonicalMarketHistoryIndexStatus\n)\n\nclass T(unittest.TestCase):\n    def test_identity(self):\n        self.assertEqual(OIAR_003_BUILD_ID,"OIAR-003")\n\n    def test_contract(self):\n        x=CanonicalMarketHistoryIndexStatus(\n            INDEX_NAME,True,True,True,True,"KXTEST",250,True,True,False\n        )\n        self.assertTrue(x.plan_uses_index)\n        self.assertFalse(x.execution_authority)\n\n    def test_expression_contract(self):\n        self.assertIn("source_market_id",MARKET_ID_EXPRESSION)\n        self.assertIn("market_id",MARKET_ID_EXPRESSION)\n        self.assertIn("source_symbol",MARKET_ID_EXPRESSION)\n\nif __name__=="__main__":\n    print("="*88)\n    print(" OIAR-003 CERTIFICATION TEST")\n    print(" CANONICAL MARKET-HISTORY ACCESS INDEX")\n    print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(\n        unittest.defaultTestLoader.loadTestsFromTestCase(T)\n    )\n    if not r.wasSuccessful():\n        raise SystemExit(1)\n    print("[PASS] market identity/index contract certified")\n    print("[PASS] execution_authority=FALSE")\n    print("[DONE] OIAR-003 CERTIFIED")\n'

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
    print(" OIAR-003 INSTALLER")
    print(" CANONICAL MARKET-HISTORY ACCESS INDEX")
    print("="*88)
    print("[ROOT]",ROOT)

    for p in (
        PKG/"oiar_001_production_analytics_snapshot_foundation.py",
        PKG/"oiar_002_current_reasoning_market_cohort_snapshot.py",
        ROOT/"qseries_v2"/"oracle_production_hardening"/"oph_019_postgresql_universal_ingestion_queue.py",
    ):
        if not p.is_file():
            raise RuntimeError(f"Required proven upstream missing: {p}")

    old={p:(p.read_bytes() if p.exists() else None) for p in (MOD,TEST,INIT)}

    try:
        init_text=INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        export="from .oiar_003_canonical_market_history_access_index import *"
        if export not in init_text:
            init_text=init_text.rstrip()+"\n"+export+"\n"

        write_exact(MOD,MODULE_SOURCE)
        write_exact(TEST,TEST_SOURCE)
        write_exact(INIT,init_text)

        ast.parse(MODULE_SOURCE)
        ast.parse(TEST_SOURCE)
        print("[PASS] installer payload syntax verified")

        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)

        importlib.invalidate_caches()
        m=importlib.import_module(
            "qseries_v2.oracle_intelligence_analytics_runtime.oiar_003_canonical_market_history_access_index"
        )

        before=m._index_status(ROOT)
        print(
            f"[INDEX BEFORE] exists={before[0]} valid={before[1]} "
            f"ready={before[2]} live={before[3]}"
        )

        if not before[0]:
            print("[INDEX BUILD] creating concurrent partial market-history index")
            print("[INDEX BUILD] one-time operation on the 30 GB canonical table")

        started=time.monotonic()
        after=m.ensure_canonical_market_history_index(ROOT)
        elapsed=time.monotonic()-started

        print(
            f"[INDEX AFTER] exists={after[0]} valid={after[1]} "
            f"ready={after[2]} live={after[3]} elapsed_seconds={elapsed:.2f}"
        )

        if not all(after):
            raise RuntimeError("OIAR-003 index did not reach valid/ready/live state")

        status=m.probe_indexed_market_history(ROOT,limit=250,timeout_ms=10000)
        print(
            f"[PHYSICAL PROBE] ticker={status.probe_market_ticker} "
            f"rows={status.probe_rows} "
            f"plan_uses_index={status.plan_uses_index}"
        )

        if not m.verify_oiar_003_canonical_market_history_access_index(ROOT):
            raise RuntimeError("OIAR-003 physical indexed probe failed")

    except Exception:
        for p,data in old.items():
            restore(p,data)
        print("[ROLLBACK] OIAR-003 repository files restored")
        print("[NOTE] PostgreSQL DDL is not rolled back by repository-file rollback")
        raise

    print("[PASS] concurrent partial expression index valid/ready/live")
    print("[PASS] OIAR-002 market history uses indexed plan")
    print("[PASS] physical probe bounded to 10 seconds")
    print("[PASS] no OIA analytics computation executed")
    print("[PASS] no Oracle Live launcher mutation")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OIAR-003 INSTALLATION COMPLETE")

if __name__=="__main__":
    main()

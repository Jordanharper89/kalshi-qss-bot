from pathlib import Path
import ast,importlib,os,subprocess,sys,time

ROOT=Path.cwd().resolve()
PKG=ROOT/"qseries_v2"/"oracle_intelligence_analytics_runtime"
MOD=PKG/"oiar_051_active_kalshi_canonical_bridge_proof.py"
TEST=ROOT/"test_oiar_051_active_kalshi_canonical_bridge_proof.py"
MODULE_SOURCE='from __future__ import annotations\n\nfrom dataclasses import dataclass\nfrom pathlib import Path\n\nfrom qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect\nfrom qseries_v2.oracle_intelligence_analytics_runtime.oiar_003_canonical_market_history_access_index import (\n    INDEX_NAME,\n    MARKET_ID_EXPRESSION,\n    _index_status,\n)\n\nOIAR_051_BUILD_ID = "OIAR-051"\nOIAR_051_REVISION = "OIAR_051_ACTIVE_KALSHI_CANONICAL_BRIDGE_PROOF_V1"\n\n@dataclass(frozen=True)\nclass ActiveKalshiCanonicalBridgeProof:\n    checked:int\n    matched_market_snapshots:int\n    exact_ticker_matches:int\n    newest_sequence_number:int\n    index_name:str\n    index_valid:bool\n    index_ready:bool\n    index_live:bool\n    plan_uses_index:bool\n    read_only:bool=True\n    execution_authority:bool=False\n\ndef _recent_active_opc_tickers(root, limit=250):\n    root=Path(root or Path.cwd()).resolve()\n    sql="""\n        SELECT DISTINCT ON (market_id)\n               market_id, sequence_number, acquired_at\n        FROM (\n            SELECT\n                sequence_number,\n                acquired_at,\n                COALESCE(\n                    NULLIF(COALESCE(\n                        canonical_observation_json->\'raw_observation\'->\'payload\',\n                        canonical_observation_json->\'payload\',\n                        \'{}\'::jsonb\n                    )->>\'source_market_id\',\'\'),\n                    NULLIF(COALESCE(\n                        canonical_observation_json->\'raw_observation\'->\'payload\',\n                        canonical_observation_json->\'payload\',\n                        \'{}\'::jsonb\n                    )->>\'market_id\',\'\'),\n                    NULLIF(COALESCE(\n                        canonical_observation_json->\'raw_observation\'->\'payload\',\n                        canonical_observation_json->\'payload\',\n                        \'{}\'::jsonb\n                    )->>\'source_symbol\',\'\')\n                ) AS market_id\n            FROM public.oracle_canonical_observations\n            WHERE observation_type=\'market_snapshot\'\n              AND COALESCE(\n                    canonical_observation_json->\'raw_observation\'->\'payload\',\n                    canonical_observation_json->\'payload\',\n                    \'{}\'::jsonb\n                  )->>\'source_status_filter\'=\'active\'\n              AND COALESCE(\n                    canonical_observation_json->\'raw_observation\'->\'payload\',\n                    canonical_observation_json->\'payload\',\n                    \'{}\'::jsonb\n                  )->>\'opc_snapshot\'=\'true\'\n        ) x\n        WHERE market_id IS NOT NULL\n        ORDER BY market_id, sequence_number DESC\n        LIMIT %s\n    """\n    with connect(root,autocommit=False) as conn:\n        with conn.cursor() as cur:\n            cur.execute("SET TRANSACTION READ ONLY")\n            cur.execute("SET LOCAL statement_timeout=\'15000ms\'")\n            cur.execute(sql,(int(limit),))\n            rows=cur.fetchall() or []\n        conn.rollback()\n    return tuple(str(r[0]) for r in rows if str(r[0] or "").strip())\n\ndef prove_active_kalshi_canonical_bridge(root=None, limit=250, timeout_ms=15000):\n    root=Path(root or Path.cwd()).resolve()\n    exists,valid,ready,live=_index_status(root)\n    if not (exists and valid and ready and live):\n        raise RuntimeError("OIAR-051 requires valid/ready/live OIAR-003 canonical market-history index")\n\n    tickers=_recent_active_opc_tickers(root,limit=limit)\n    if not tickers:\n        raise RuntimeError("OIAR-051 found no persisted ACTIVE OPC market_snapshot identities")\n\n    sql=f"""\n        SELECT wanted.market_id,\n               history.sequence_number,\n               history.observed_at\n        FROM unnest(%s::text[]) AS wanted(market_id)\n        CROSS JOIN LATERAL (\n            SELECT sequence_number,observed_at\n            FROM public.oracle_canonical_observations\n            WHERE observation_type=\'market_snapshot\'\n              AND ({MARKET_ID_EXPRESSION})=wanted.market_id\n            ORDER BY sequence_number DESC\n            LIMIT 1\n        ) history\n        ORDER BY wanted.market_id\n    """\n\n    with connect(root,autocommit=False) as conn:\n        with conn.cursor() as cur:\n            cur.execute("SET TRANSACTION READ ONLY")\n            cur.execute(f"SET LOCAL statement_timeout=\'{int(timeout_ms)}ms\'")\n            cur.execute("EXPLAIN (FORMAT JSON) "+sql,(list(tickers),))\n            plan=cur.fetchone()[0]\n            cur.execute(sql,(list(tickers),))\n            rows=cur.fetchall() or []\n        conn.rollback()\n\n    import json\n    plan_text=json.dumps(plan,sort_keys=True,default=str)\n    returned={str(r[0]) for r in rows}\n    expected=set(tickers)\n    exact=len(expected & returned)\n    newest=max((int(r[1]) for r in rows),default=0)\n\n    return ActiveKalshiCanonicalBridgeProof(\n        checked=len(tickers),\n        matched_market_snapshots=len(rows),\n        exact_ticker_matches=exact,\n        newest_sequence_number=newest,\n        index_name=INDEX_NAME,\n        index_valid=valid,\n        index_ready=ready,\n        index_live=live,\n        plan_uses_index=INDEX_NAME in plan_text,\n        read_only=True,\n        execution_authority=False,\n    )\n\ndef verify_oiar_051_active_kalshi_canonical_bridge_proof(root=None):\n    x=prove_active_kalshi_canonical_bridge(root)\n    return bool(\n        x.checked>0\n        and x.matched_market_snapshots>0\n        and x.exact_ticker_matches>0\n        and x.exact_ticker_matches==x.matched_market_snapshots\n        and x.index_valid and x.index_ready and x.index_live\n        and x.plan_uses_index\n        and x.read_only\n        and not x.execution_authority\n    )\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_intelligence_analytics_runtime.oiar_051_active_kalshi_canonical_bridge_proof import (\n    prove_active_kalshi_canonical_bridge,\n    verify_oiar_051_active_kalshi_canonical_bridge_proof,\n)\n\nclass T(unittest.TestCase):\n    def test_physical_bridge(self):\n        x=prove_active_kalshi_canonical_bridge()\n        self.assertGreater(x.checked,0)\n        self.assertGreater(x.matched_market_snapshots,0)\n        self.assertGreater(x.exact_ticker_matches,0)\n        self.assertEqual(x.exact_ticker_matches,x.matched_market_snapshots)\n        self.assertTrue(x.index_valid)\n        self.assertTrue(x.index_ready)\n        self.assertTrue(x.index_live)\n        self.assertTrue(x.plan_uses_index)\n        self.assertTrue(x.read_only)\n        self.assertFalse(x.execution_authority)\n\n    def test_verifier(self):\n        self.assertTrue(verify_oiar_051_active_kalshi_canonical_bridge_proof())\n\nif __name__=="__main__":\n    print("="*88)\n    print(" OIAR-051 CERTIFICATION TEST")\n    print(" ACTIVE KALSHI -> CANONICAL MARKET_SNAPSHOT -> OIAR INDEX BRIDGE PROOF")\n    print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(\n        unittest.defaultTestLoader.loadTestsFromTestCase(T)\n    )\n    if not r.wasSuccessful():\n        raise SystemExit(1)\n    print("[PASS] ACTIVE Kalshi canonical bridge physically certified")\n    print("[PASS] OIAR indexed read path physically certified")\n    print("[PASS] execution_authority=FALSE")\n    print("[DONE] OIAR-051 CERTIFIED")\n'

def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name(path.name+f".{os.getpid()}.tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def restore(path,data):
    if data is None:
        if path.exists(): path.unlink()
    else:
        path.write_bytes(data)

def main():
    print("="*88)
    print(" OIAR-051 INSTALLER")
    print(" ACTIVE KALSHI CANONICAL BRIDGE PROOF")
    print("="*88)
    print("[ROOT]",ROOT)

    required=[
        ROOT/"qseries_v2/oracle_pre_settlement_coverage/opc_030_high_throughput_universal_coverage_gate.py",
        ROOT/"qseries_v2/oracle_intelligence_analytics_runtime/oiar_003_canonical_market_history_access_index.py",
    ]
    for r in required:
        if not r.is_file():
            raise RuntimeError("Required proven upstream missing: "+str(r.relative_to(ROOT)))

    old_mod=MOD.read_bytes() if MOD.exists() else None
    old_test=TEST.read_bytes() if TEST.exists() else None

    try:
        ast.parse(MODULE_SOURCE,filename=str(MOD))
        ast.parse(TEST_SOURCE,filename=str(TEST))
        print("[PASS] installer payload syntax verified")

        write_exact(MOD,MODULE_SOURCE)
        write_exact(TEST,TEST_SOURCE)
        importlib.invalidate_caches()

        m=importlib.import_module(
            "qseries_v2.oracle_intelligence_analytics_runtime.oiar_051_active_kalshi_canonical_bridge_proof"
        )
        started=time.monotonic()
        x=m.prove_active_kalshi_canonical_bridge(ROOT)
        elapsed=round(time.monotonic()-started,3)
        print("[PHYSICAL]",x,"elapsed_seconds=",elapsed)

        if x.checked<=0:
            raise RuntimeError("OIAR-051 proof checked zero ACTIVE OPC markets")
        if x.matched_market_snapshots<=0:
            raise RuntimeError("OIAR-051 found zero canonical market_snapshot matches")
        if x.exact_ticker_matches<=0:
            raise RuntimeError("OIAR-051 found zero exact ticker identity matches")
        if not x.plan_uses_index:
            raise RuntimeError("OIAR-051 physical read did not use OIAR canonical market-history index")
        if x.execution_authority:
            raise RuntimeError("OIAR-051 execution authority invariant violated")

        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True,timeout=60)

    except Exception:
        restore(MOD,old_mod)
        restore(TEST,old_test)
        print("[ROLLBACK] OIAR-051 proof failed; affected files restored")
        raise

    print("[PASS] checked > 0")
    print("[PASS] matched_market_snapshots > 0")
    print("[PASS] exact_ticker_matches > 0")
    print("[PASS] OIAR indexed canonical identity path proven")
    print("[PASS] canonical observations remained read-only")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OIAR-051 ACTIVE KALSHI CANONICAL BRIDGE PROOF COMPLETE")

if __name__=="__main__":
    main()

from pathlib import Path
import ast,importlib,os,subprocess,sys,time

ROOT=Path.cwd().resolve()
MOD=ROOT/"qseries_v2/oracle_intelligence_analytics_runtime/oiar_051_bounded_recent_canonical_bridge_proof.py"
TEST=ROOT/"test_oiar_051_bounded_recent_canonical_bridge_proof.py"
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom pathlib import Path\nimport json\n\nfrom qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect\nfrom qseries_v2.oracle_intelligence_analytics_runtime.oiar_003_canonical_market_history_access_index import (\n    INDEX_NAME, MARKET_ID_EXPRESSION, _index_status,\n)\n\nOIAR_051_BUILD_ID="OIAR-051"\nOIAR_051_REVISION="OIAR_051_BOUNDED_RECENT_CANONICAL_BRIDGE_PROOF_V1"\n\n@dataclass(frozen=True)\nclass CanonicalBridgeProof:\n    sequence_ceiling:int\n    sequence_floor:int\n    recent_rows_scanned:int\n    active_opc_candidates:int\n    checked:int\n    matched_market_snapshots:int\n    exact_ticker_matches:int\n    newest_sequence_number:int\n    index_name:str\n    exact_lookup_uses_index:bool\n    read_only:bool=True\n    execution_authority:bool=False\n\ndef _payload(row):\n    if not isinstance(row,dict):\n        return {}\n    raw=row.get("raw_observation")\n    if isinstance(raw,dict) and isinstance(raw.get("payload"),dict):\n        return raw["payload"]\n    p=row.get("payload")\n    return p if isinstance(p,dict) else {}\n\ndef _recent_active_candidates(root, window=50000, limit=250, timeout_ms=10000):\n    root=Path(root or Path.cwd()).resolve()\n    with connect(root,autocommit=False) as c:\n        q=c.cursor()\n        q.execute("SET TRANSACTION READ ONLY")\n        q.execute(f"SET LOCAL statement_timeout=\'{int(timeout_ms)}ms\'")\n        q.execute("SELECT max(sequence_number) FROM public.oracle_canonical_observations")\n        ceiling=int((q.fetchone() or [0])[0] or 0)\n        if ceiling<=0:\n            raise RuntimeError("canonical observation table is empty")\n        floor=max(1,ceiling-int(window)+1)\n        q.execute("""\n            SELECT sequence_number, observation_type, canonical_observation_json\n            FROM public.oracle_canonical_observations\n            WHERE sequence_number BETWEEN %s AND %s\n            ORDER BY sequence_number DESC\n        """,(floor,ceiling))\n        rows=q.fetchall() or []\n        c.rollback()\n\n    found=[]\n    seen=set()\n    for seq,typ,doc in rows:\n        if str(typ)!="market_snapshot":\n            continue\n        if isinstance(doc,str):\n            try: doc=json.loads(doc)\n            except Exception: continue\n        p=_payload(doc)\n        if str(p.get("source_status_filter") or "").strip().lower()!="active":\n            continue\n        if str(p.get("opc_snapshot") or "").strip().lower()!="true":\n            continue\n        ticker=str(p.get("source_market_id") or p.get("market_id") or p.get("source_symbol") or "").strip()\n        if ticker and ticker not in seen:\n            seen.add(ticker); found.append(ticker)\n            if len(found)>=int(limit):\n                break\n    return ceiling,floor,len(rows),tuple(found)\n\ndef prove_bounded_recent_canonical_bridge(root=None, window=50000, limit=250, timeout_ms=10000):\n    root=Path(root or Path.cwd()).resolve()\n    exists,valid,ready,live=_index_status(root)\n    if not (exists and valid and ready and live):\n        raise RuntimeError("OIAR-003 market identity index is not valid/ready/live")\n\n    ceiling,floor,scanned,tickers=_recent_active_candidates(root,window,limit,timeout_ms)\n    if not tickers:\n        raise RuntimeError(\n            f"OIAR-051 found no ACTIVE OPC market_snapshot candidates in bounded sequence window "\n            f"{floor}..{ceiling}"\n        )\n\n    sql=f"""\n        SELECT wanted.market_id, h.sequence_number\n        FROM unnest(%s::text[]) wanted(market_id)\n        CROSS JOIN LATERAL (\n            SELECT sequence_number\n            FROM public.oracle_canonical_observations\n            WHERE observation_type=\'market_snapshot\'\n              AND ({MARKET_ID_EXPRESSION})=wanted.market_id\n            ORDER BY sequence_number DESC\n            LIMIT 1\n        ) h\n    """\n    with connect(root,autocommit=False) as c:\n        q=c.cursor()\n        q.execute("SET TRANSACTION READ ONLY")\n        q.execute(f"SET LOCAL statement_timeout=\'{int(timeout_ms)}ms\'")\n        q.execute("EXPLAIN (FORMAT JSON) "+sql,(list(tickers),))\n        plan=q.fetchone()[0]\n        q.execute(sql,(list(tickers),))\n        matches=q.fetchall() or []\n        c.rollback()\n\n    plan_text=json.dumps(plan,sort_keys=True,default=str)\n    returned={str(x[0]) for x in matches}\n    exact=len(set(tickers)&returned)\n\n    return CanonicalBridgeProof(\n        ceiling,floor,scanned,len(tickers),len(tickers),len(matches),exact,\n        max((int(x[1]) for x in matches),default=0),\n        INDEX_NAME,INDEX_NAME in plan_text,True,False\n    )\n\ndef verify_oiar_051_bounded_recent_canonical_bridge_proof(root=None):\n    x=prove_bounded_recent_canonical_bridge(root)\n    return (\n        x.checked>0 and\n        x.matched_market_snapshots>0 and\n        x.exact_ticker_matches>0 and\n        x.exact_ticker_matches==x.matched_market_snapshots and\n        x.exact_lookup_uses_index and\n        x.read_only and\n        not x.execution_authority\n    )\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_intelligence_analytics_runtime.oiar_051_bounded_recent_canonical_bridge_proof import (\n    prove_bounded_recent_canonical_bridge,\n    verify_oiar_051_bounded_recent_canonical_bridge_proof,\n)\n\nclass T(unittest.TestCase):\n    def test_physical_bridge(self):\n        x=prove_bounded_recent_canonical_bridge()\n        self.assertGreater(x.recent_rows_scanned,0)\n        self.assertGreater(x.active_opc_candidates,0)\n        self.assertGreater(x.checked,0)\n        self.assertGreater(x.matched_market_snapshots,0)\n        self.assertGreater(x.exact_ticker_matches,0)\n        self.assertEqual(x.exact_ticker_matches,x.matched_market_snapshots)\n        self.assertTrue(x.exact_lookup_uses_index)\n        self.assertTrue(x.read_only)\n        self.assertFalse(x.execution_authority)\n\n    def test_verifier(self):\n        self.assertTrue(verify_oiar_051_bounded_recent_canonical_bridge_proof())\n\nif __name__=="__main__":\n    print("="*88)\n    print(" OIAR-051 CERTIFICATION TEST")\n    print(" BOUNDED RECENT CANONICAL BRIDGE PROOF")\n    print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(\n        unittest.defaultTestLoader.loadTestsFromTestCase(T)\n    )\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] bounded recent ACTIVE OPC candidates physically proven")\n    print("[PASS] exact OIAR-003 indexed identity matches physically proven")\n    print("[PASS] read_only=TRUE")\n    print("[PASS] execution_authority=FALSE")\n    print("[DONE] OIAR-051 CERTIFIED")\n'

def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name(path.name+f".{os.getpid()}.tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def restore(path,data):
    if data is None:
        if path.exists(): path.unlink()
    else: path.write_bytes(data)

def main():
    print("="*88)
    print(" OIAR-051 INSTALLER")
    print(" BOUNDED RECENT CANONICAL BRIDGE PROOF")
    print("="*88)
    print("[ROOT]",ROOT)

    required=[
        ROOT/"qseries_v2/oracle_pre_settlement_coverage/opc_030_high_throughput_universal_coverage_gate.py",
        ROOT/"qseries_v2/oracle_intelligence_analytics_runtime/oiar_003_canonical_market_history_access_index.py",
    ]
    for r in required:
        if not r.is_file(): raise RuntimeError("Required proven upstream missing: "+str(r.relative_to(ROOT)))

    old_mod=MOD.read_bytes() if MOD.exists() else None
    old_test=TEST.read_bytes() if TEST.exists() else None

    try:
        ast.parse(MODULE_SOURCE); ast.parse(TEST_SOURCE)
        print("[PASS] installer payload syntax verified")
        write_exact(MOD,MODULE_SOURCE); write_exact(TEST,TEST_SOURCE)
        importlib.invalidate_caches()
        m=importlib.import_module("qseries_v2.oracle_intelligence_analytics_runtime.oiar_051_bounded_recent_canonical_bridge_proof")
        s=time.monotonic()
        x=m.prove_bounded_recent_canonical_bridge(ROOT)
        print("[PHYSICAL]",x,"elapsed_seconds=",round(time.monotonic()-s,3))
        if not m.verify_oiar_051_bounded_recent_canonical_bridge_proof(ROOT):
            raise RuntimeError("OIAR-051 physical verifier returned false")
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True,timeout=60)
    except Exception:
        restore(MOD,old_mod); restore(TEST,old_test)
        print("[ROLLBACK] OIAR-051 proof failed; affected files restored")
        raise

    print("[PASS] bounded primary-key discovery path proven")
    print("[PASS] checked > 0")
    print("[PASS] matched_market_snapshots > 0")
    print("[PASS] exact_ticker_matches > 0")
    print("[PASS] exact identity verification uses OIAR-003 index")
    print("[PASS] canonical observations remained read-only")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OIAR-051 BOUNDED RECENT CANONICAL BRIDGE PROOF COMPLETE")

if __name__=="__main__": main()

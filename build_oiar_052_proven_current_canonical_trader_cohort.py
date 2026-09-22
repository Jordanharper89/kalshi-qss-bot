from pathlib import Path
import ast,importlib,os,subprocess,sys,time

ROOT=Path.cwd().resolve()
MOD=ROOT/'qseries_v2/oracle_intelligence_analytics_runtime/oiar_052_proven_current_canonical_trader_cohort.py'
TEST=ROOT/'test_oiar_052_proven_current_canonical_trader_cohort.py'
MODULE_SOURCE='from __future__ import annotations\nfrom datetime import datetime,timezone\nfrom pathlib import Path\nimport json\nfrom qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect\nfrom .oiar_001_production_analytics_snapshot_foundation import SNAPSHOT_TABLE,stable_hash\nfrom .oiar_003_canonical_market_history_access_index import MARKET_ID_EXPRESSION,INDEX_NAME,_index_status\nfrom .oiar_051_bounded_recent_canonical_bridge_proof import _recent_active_candidates\n\nOIAR_052_BUILD_ID="OIAR-052"\nOIAR_052_REVISION="OIAR_052_PROVEN_CURRENT_CANONICAL_TRADER_COHORT_V1"\nSTAGE="proven_current_canonical_trader_cohort"\n\ndef _p(doc):\n    if not isinstance(doc,dict):return {}\n    raw=doc.get("raw_observation")\n    if isinstance(raw,dict) and isinstance(raw.get("payload"),dict):return raw["payload"]\n    p=doc.get("payload");return p if isinstance(p,dict) else {}\n\ndef materialize_current_trader_cohort(root=None,limit=100,window=50000,timeout_ms=15000):\n    root=Path(root or Path.cwd()).resolve()\n    if not all(_index_status(root)):raise RuntimeError("OIAR-052 requires valid OIAR-003 index")\n    ceiling,floor,scanned,tickers=_recent_active_candidates(root,window,max(limit*3,250),timeout_ms)\n    if not tickers:raise RuntimeError("OIAR-052 no proven ACTIVE OPC candidates")\n    sql=f"""SELECT wanted.market_id,h.sequence_number,h.observed_at,h.canonical_observation_json\n    FROM unnest(%s::text[]) wanted(market_id)\n    CROSS JOIN LATERAL(\n      SELECT sequence_number,observed_at,canonical_observation_json\n      FROM public.oracle_canonical_observations\n      WHERE observation_type=\'market_snapshot\' AND ({MARKET_ID_EXPRESSION})=wanted.market_id\n      ORDER BY sequence_number DESC LIMIT 1\n    ) h ORDER BY h.sequence_number DESC LIMIT %s"""\n    with connect(root,autocommit=False) as c:\n        q=c.cursor();q.execute("SET TRANSACTION READ ONLY");q.execute(f"SET LOCAL statement_timeout=\'{int(timeout_ms)}ms\'")\n        q.execute(sql,(list(tickers),int(limit)));rows=q.fetchall() or [];c.rollback()\n    markets=[]\n    for ticker,seq,obs,doc in rows:\n        if isinstance(doc,str):doc=json.loads(doc)\n        p=_p(doc)\n        markets.append({"market_ticker":str(ticker),"event_ticker":str(p.get("event_ticker") or ""),\n          "title":str(p.get("title") or p.get("market_title") or ""), "status":str(p.get("status") or p.get("source_status_filter") or "active").lower(),\n          "close_time":p.get("close_time") or p.get("expected_expiration_time") or p.get("expiration_time"),\n          "latest_sequence_number":int(seq),"latest_observed_at":str(obs),"source_index":INDEX_NAME})\n    if not markets:raise RuntimeError("OIAR-052 produced empty cohort")\n    body={"schema_version":"OIAR-052","stage":STAGE,"market_count":len(markets),"sequence_floor":floor,"sequence_ceiling":ceiling,\n          "recent_rows_scanned":scanned,"markets":markets,"read_only_source":True,"execution_authority":False}\n    h=stable_hash(body);sid="oiar-052-"+h[:32]\n    with connect(root,autocommit=False) as c:\n        q=c.cursor();q.execute(f"""INSERT INTO public.{SNAPSHOT_TABLE}(snapshot_id,stage,source_schema_version,source_engine_id,generated_at,market_count,payload_json,payload_hash,read_only_source,execution_authority)\n        VALUES(%s,%s,%s,%s,%s,%s,%s::jsonb,%s,TRUE,FALSE) ON CONFLICT(snapshot_id) DO NOTHING""",\n        (sid,STAGE,"OIAR-052",OIAR_052_BUILD_ID,datetime.now(timezone.utc),len(markets),json.dumps(body,sort_keys=True,separators=(",",":"),default=str),h));c.commit()\n    return body\n\ndef read_latest_current_trader_cohort(root=None):\n    root=Path(root or Path.cwd()).resolve()\n    with connect(root,autocommit=False) as c:\n        q=c.cursor();q.execute("SET TRANSACTION READ ONLY");q.execute(f"SELECT payload_json,payload_hash FROM public.{SNAPSHOT_TABLE} WHERE stage=%s ORDER BY generated_at DESC,persisted_at DESC LIMIT 1",(STAGE,));r=q.fetchone();c.rollback()\n    if not r:return None\n    p,h=r\n    if isinstance(p,str):p=json.loads(p)\n    if stable_hash(p)!=str(h):raise RuntimeError("OIAR-052 snapshot hash mismatch")\n    return p\n\ndef physical_probe(root=None):return materialize_current_trader_cohort(root)\n'
TEST_SOURCE='import unittest\nimport qseries_v2.oracle_intelligence_analytics_runtime.oiar_052_proven_current_canonical_trader_cohort as m\nclass T(unittest.TestCase):\n def test_identity(self):self.assertEqual(m.OIAR_052_BUILD_ID,"OIAR-052")\n def test_stage(self):self.assertEqual(m.STAGE,"proven_current_canonical_trader_cohort")\n def test_physical(self):\n  x=m.read_latest_current_trader_cohort();self.assertTrue(x);self.assertGreater(x["market_count"],0);self.assertFalse(x["execution_authority"])\nif __name__=="__main__":\n print("="*88);print(" OIAR-052 CERTIFICATION TEST");print(" PROVEN CURRENT CANONICAL TRADER COHORT");print("="*88)\n r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n if not r.wasSuccessful():raise SystemExit(1)\n print("[PASS] current canonical cohort certified");print("[DONE] OIAR-052 CERTIFIED")\n'
REQUIRED=('qseries_v2/oracle_intelligence_analytics_runtime/oiar_051_bounded_recent_canonical_bridge_proof.py', 'qseries_v2/oracle_intelligence_analytics_runtime/oiar_003_canonical_market_history_access_index.py')
EXTRA_FILES={}

def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name(path.name+f".{os.getpid()}.tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def restore(path,data):
    if data is None:
        if path.exists(): path.unlink()
    else:
        path.parent.mkdir(parents=True,exist_ok=True); path.write_bytes(data)

def main():
    print("="*88);print(" OIAR-052 INSTALLER");print(" PROVEN CURRENT CANONICAL TRADER COHORT");print("="*88);print("[ROOT]",ROOT)
    for rel in REQUIRED:
        p=ROOT/rel
        if not p.is_file(): raise RuntimeError("Required proven upstream missing: "+rel)
    targets=[MOD,TEST]+[ROOT/x for x in EXTRA_FILES]
    old={p:(p.read_bytes() if p.exists() else None) for p in targets}
    try:
        ast.parse(MODULE_SOURCE);ast.parse(TEST_SOURCE)
        for src in EXTRA_FILES.values():ast.parse(src)
        print("[PASS] installer payload syntax verified")
        write_exact(MOD,MODULE_SOURCE);write_exact(TEST,TEST_SOURCE)
        for rel,src in EXTRA_FILES.items():write_exact(ROOT/rel,src)
        importlib.invalidate_caches()
        m=importlib.import_module("qseries_v2.oracle_intelligence_analytics_runtime.oiar_052_proven_current_canonical_trader_cohort")
        s=time.monotonic()
        x=m.physical_probe(ROOT)
        print("[PHYSICAL]",x,"elapsed_seconds=",round(time.monotonic()-s,3))
        if x["market_count"]<=0:raise RuntimeError("OIAR-052 empty physical cohort")
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True,timeout=120)
    except Exception:
        for p,data in old.items():restore(p,data)
        print("[ROLLBACK] OIAR-052 failed; affected files restored")
        raise
    print("[PASS] read-only intelligence boundary preserved")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OIAR-052 INSTALLATION COMPLETE")
if __name__=="__main__":main()

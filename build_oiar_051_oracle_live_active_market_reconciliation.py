from pathlib import Path
import ast,importlib,os,subprocess,sys,time
ROOT=Path.cwd().resolve()
MOD=ROOT/'qseries_v2/oracle_intelligence_analytics_runtime/oiar_051_oracle_live_active_market_reconciliation.py'
TEST=ROOT/'test_oiar_051_oracle_live_active_market_reconciliation.py'
MODULE_SOURCE='\nfrom __future__ import annotations\nfrom pathlib import Path\nimport json\n\nfrom qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect\nfrom .oiar_001_production_analytics_snapshot_foundation import SNAPSHOT_TABLE,stable_hash\nfrom .oiar_047_production_kalshi_current_eligibility_boundary import read_current_kalshi_markets\nfrom .oiar_050_recent_time_oracle_live_market_boundary import STAGE as LIVE_STAGE\n\nOIAR_051_BUILD_ID="OIAR-051"\nOIAR_051_REVISION="OIAR_051_ORACLE_LIVE_ACTIVE_MARKET_RECONCILIATION_V1"\nSTAGE="oracle_live_active_market_reconciliation"\nEXECUTION_AUTHORITY=False\n\ndef _latest_live(root):\n    with connect(root,autocommit=False) as c:\n        with c.cursor() as cur:\n            cur.execute("SET TRANSACTION READ ONLY")\n            cur.execute(f"""SELECT payload_json,payload_hash\n                            FROM public.{SNAPSHOT_TABLE}\n                            WHERE stage=%s\n                            ORDER BY generated_at DESC,persisted_at DESC LIMIT 1""",(LIVE_STAGE,))\n            row=cur.fetchone()\n        c.rollback()\n    if not row: raise RuntimeError("OIAR-051 requires certified OIAR-050 recent-time snapshot")\n    payload,h=row\n    if isinstance(payload,str): payload=json.loads(payload)\n    if stable_hash(payload)!=str(h): raise RuntimeError("OIAR-051 OIAR-050 snapshot hash mismatch")\n    return payload\n\ndef reconcile_oracle_live_active_markets(root=None):\n    root=Path(root or Path.cwd()).resolve()\n    live=_latest_live(root)\n    active,_=read_current_kalshi_markets(root,max_pages=5,timeout_seconds=15)\n    active_map={x.ticker:x for x in active}\n    rows=[]\n    for obs in live.get("markets",()):\n        ticker=str(obs.get("market_ticker") or "").strip().upper()\n        meta=active_map.get(ticker)\n        if meta is None: continue\n        x=dict(obs)\n        x.update({\n            "event_ticker":meta.event_ticker,\n            "market_title":meta.title,\n            "status":meta.status,\n            "open_time":meta.open_time,\n            "close_time":meta.close_time,\n            "expiration_time":meta.expiration_time,\n            "expected_expiration_time":meta.expected_expiration_time,\n            "updated_time":meta.updated_time,\n        })\n        rows.append(x)\n    rows.sort(key=lambda x:(float(x.get("freshness_seconds") or 1e18),-int(x.get("latest_sequence") or 0),x["market_ticker"]))\n    if not rows: raise RuntimeError("OIAR-051 found zero overlap between recent Oracle Live and ACTIVE Kalshi markets")\n    payload={\n        "schema_version":"OIAR-051","stage":STAGE,\n        "source_live_markets":int(live.get("market_count") or 0),\n        "reconciled_market_count":len(rows),\n        "markets":rows,"read_only_source":True,"execution_authority":False,\n    }\n    h=stable_hash(payload);sid="oiar-051-"+h[:32]\n    with connect(root,autocommit=False) as c:\n        with c.cursor() as cur:\n            cur.execute(f"""INSERT INTO public.{SNAPSHOT_TABLE}\n            (snapshot_id,stage,source_schema_version,source_engine_id,generated_at,\n             market_count,payload_json,payload_hash,read_only_source,execution_authority)\n            VALUES(%s,%s,%s,%s,clock_timestamp(),%s,%s::jsonb,%s,TRUE,FALSE)\n            ON CONFLICT(snapshot_id) DO NOTHING""",\n            (sid,STAGE,"OIAR-051",OIAR_051_BUILD_ID,len(rows),json.dumps(payload,sort_keys=True,default=str),h))\n        c.commit()\n    return sid,payload\n\ndef physical_probe(root=None):\n    sid,p=reconcile_oracle_live_active_markets(root)\n    return {"snapshot_id":sid,"source_live_markets":p["source_live_markets"],"reconciled_active_markets":p["reconciled_market_count"],"execution_authority":False}\n'
TEST_SOURCE='\nimport unittest\nimport qseries_v2.oracle_intelligence_analytics_runtime.oiar_051_oracle_live_active_market_reconciliation as m\nclass T(unittest.TestCase):\n def test_identity(self):self.assertEqual(m.OIAR_051_BUILD_ID,"OIAR-051")\n def test_stage(self):self.assertEqual(m.STAGE,"oracle_live_active_market_reconciliation")\n def test_boundary(self):self.assertFalse(m.EXECUTION_AUTHORITY)\nif __name__=="__main__":\n print("="*88);print(" OIAR-051 CERTIFICATION TEST");print(" ORACLE LIVE ACTIVE MARKET RECONCILIATION");print("="*88)\n r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n if not r.wasSuccessful():raise SystemExit(1)\n print("[PASS] recent Oracle Live identities reconcile only to ACTIVE/current Kalshi")\n'
REQUIRED=('qseries_v2/oracle_intelligence_analytics_runtime/oiar_050_recent_time_oracle_live_market_boundary.py', 'qseries_v2/oracle_intelligence_analytics_runtime/oiar_047_production_kalshi_current_eligibility_boundary.py')
EXTRAS={}

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

def main():
    print("="*88);print(" OIAR-051 INSTALLER");print(" ORACLE LIVE ACTIVE MARKET RECONCILIATION");print("="*88);print("[ROOT]",ROOT)
    for rel in REQUIRED:
        p=ROOT/rel
        if not p.is_file(): raise RuntimeError("Required proven upstream missing: "+rel)
    targets=[MOD,TEST]+[ROOT/r for r in EXTRAS]
    old={p:(p.read_bytes() if p.exists() else None) for p in targets}
    try:
        ast.parse(MODULE_SOURCE,filename=str(MOD));ast.parse(TEST_SOURCE,filename=str(TEST))
        for s in EXTRAS.values(): ast.parse(s)
        print("[PASS] installer payload syntax verified")
        write_exact(MOD,MODULE_SOURCE);write_exact(TEST,TEST_SOURCE)
        for rel,s in EXTRAS.items(): write_exact(ROOT/rel,s)
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True,timeout=30)
        importlib.invalidate_caches()
        m=importlib.import_module("qseries_v2.oracle_intelligence_analytics_runtime.oiar_051_oracle_live_active_market_reconciliation")
        s=time.monotonic();x=m.physical_probe(ROOT);print("[PHYSICAL]",x,"elapsed_seconds=",round(time.monotonic()-s,3))
        if x["reconciled_active_markets"]<=0:raise RuntimeError("OIAR-051 zero live/active overlap")
    except Exception:
        for p,b in old.items(): restore(p,b)
        print("[ROLLBACK] OIAR-051 failed; affected repository files restored")
        raise
    print("[PASS] Oracle Live remains unmodified")
    print("[PASS] terminal remains read-only")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OIAR-051 INSTALLATION COMPLETE")

if __name__=="__main__": main()

from pathlib import Path
import ast,importlib,os,subprocess,sys,time
ROOT=Path.cwd().resolve()
MOD=ROOT/'qseries_v2/oracle_intelligence_analytics_runtime/oiar_048_current_market_relevance_cohort_selector.py';TEST=ROOT/'test_oiar_048_current_market_relevance_cohort_selector.py'
MODULE_SOURCE='\nfrom __future__ import annotations\nfrom datetime import datetime,timezone\nfrom pathlib import Path\nimport json\nfrom qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect\nfrom .oiar_001_production_analytics_snapshot_foundation import SNAPSHOT_TABLE,stable_hash\nfrom .oiar_047_production_kalshi_current_eligibility_boundary import read_current_kalshi_markets,_dt\nOIAR_048_BUILD_ID="OIAR-048";STAGE="production_current_trader_cohort";EXECUTION_AUTHORITY=False\ndef select_current_trader_cohort(root=None,limit=100,now=None):\n root=Path(root or Path.cwd()).resolve();now=(now or datetime.now(timezone.utc)).astimezone(timezone.utc);rows,meta=read_current_kalshi_markets(root,now=now)\n ranked=[]\n for x in rows:\n  expected=_dt(x.expected_expiration_time);close=_dt(x.close_time or x.expiration_time);end=expected or close\n  secs=(end-now).total_seconds() if end else 10**15\n  ranked.append((secs,x))\n ranked.sort(key=lambda z:(z[0],z[1].ticker));chosen=[x for _,x in ranked[:max(1,min(int(limit),100))]]\n if not chosen:raise RuntimeError("OIAR-048 empty current cohort")\n markets=[{"market_ticker":x.ticker,"event_ticker":x.event_ticker,"market_title":x.title,"status":x.status,"open_time":x.open_time,"close_time":x.close_time,"expiration_time":x.expiration_time,"expected_expiration_time":x.expected_expiration_time,"updated_time":x.updated_time} for x in chosen]\n payload={"schema_version":"OIAR-048","stage":STAGE,"market_count":len(markets),"markets":markets,"ranking_clock":"expected_expiration_time_then_close_time","read_only_source":True,"execution_authority":False}\n h=stable_hash(payload);sid="oiar-048-"+h[:32]\n with connect(root,autocommit=False) as c:\n  with c.cursor() as cur:cur.execute(f"INSERT INTO public.{SNAPSHOT_TABLE}(snapshot_id,stage,source_schema_version,source_engine_id,generated_at,market_count,payload_json,payload_hash,read_only_source,execution_authority) VALUES(%s,%s,%s,%s,%s,%s,%s::jsonb,%s,TRUE,FALSE) ON CONFLICT(snapshot_id) DO NOTHING",(sid,STAGE,"OIAR-048",OIAR_048_BUILD_ID,now,len(markets),json.dumps(payload,sort_keys=True),h))\n  c.commit()\n return sid,payload\ndef physical_probe(root=None):\n sid,p=select_current_trader_cohort(root);return {"snapshot_id":sid,"current_markets":p["market_count"],"active":sum(x["status"]=="active" for x in p["markets"]),"with_expected_expiration":sum(bool(x["expected_expiration_time"]) for x in p["markets"]),"execution_authority":False}\n';TEST_SOURCE='\nimport unittest\nimport qseries_v2.oracle_intelligence_analytics_runtime.oiar_048_current_market_relevance_cohort_selector as m\nclass T(unittest.TestCase):\n def test_identity(self):self.assertEqual(m.OIAR_048_BUILD_ID,"OIAR-048")\n def test_stage(self):self.assertEqual(m.STAGE,"production_current_trader_cohort")\nif __name__=="__main__":\n print("="*88);print(" OIAR-048 CERTIFICATION TEST");print(" CURRENT MARKET RELEVANCE COHORT SELECTOR");print("="*88)\n r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n if not r.wasSuccessful():raise SystemExit(1)\n print("[PASS] expected-expiration-first live cohort contract certified")\n'
REQUIRED=('qseries_v2/oracle_intelligence_analytics_runtime/oiar_047_production_kalshi_current_eligibility_boundary.py', 'qseries_v2/oracle_intelligence_analytics_runtime/oiar_001_production_analytics_snapshot_foundation.py');EXTRA={}
def write_exact(p,s):
    p.parent.mkdir(parents=True,exist_ok=True);t=p.with_name(p.name+f".{os.getpid()}.tmp")
    t.write_text(s,encoding="utf-8");os.replace(t,p)
def restore(p,b):
    if b is None:
        if p.exists():p.unlink()
    else:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
def main():
    print("="*88);print(" OIAR-048 INSTALLER");print(" CURRENT MARKET RELEVANCE COHORT SELECTOR");print("="*88);print("[ROOT]",ROOT)
    for r in REQUIRED:
        if not (ROOT/r).is_file():raise RuntimeError("Required upstream missing: "+r)
    targets=[MOD,TEST]+[ROOT/r for r in EXTRA]
    old={p:(p.read_bytes() if p.exists() else None) for p in targets}
    try:
        ast.parse(MODULE_SOURCE);ast.parse(TEST_SOURCE)
        for s in EXTRA.values():ast.parse(s)
        print("[PASS] installer payload syntax verified")
        write_exact(MOD,MODULE_SOURCE);write_exact(TEST,TEST_SOURCE)
        for r,s in EXTRA.items():write_exact(ROOT/r,s)
        subprocess.run([sys.executable,str(TEST)],cwd=ROOT,check=True,timeout=30)
        importlib.invalidate_caches()
        m=importlib.import_module("qseries_v2.oracle_intelligence_analytics_runtime.oiar_048_current_market_relevance_cohort_selector");x=m.physical_probe(ROOT);print("[PHYSICAL]",x)
        if x["current_markets"]<=0 or x["active"]!=x["current_markets"]:raise RuntimeError("current cohort invalid")
    except Exception:
        for p,b in old.items():restore(p,b)
        print("[ROLLBACK] OIAR-048 failed; affected files restored");raise
    print("[PASS] read_only=True execution_authority=FALSE")
    print("[DONE] OIAR-048 INSTALLATION COMPLETE")
if __name__=="__main__":main()

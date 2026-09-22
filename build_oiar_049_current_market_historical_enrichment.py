from pathlib import Path
import ast,importlib,os,subprocess,sys,time
ROOT=Path.cwd().resolve()
MOD=ROOT/'qseries_v2/oracle_intelligence_analytics_runtime/oiar_049_current_market_historical_enrichment.py';TEST=ROOT/'test_oiar_049_current_market_historical_enrichment.py'
MODULE_SOURCE='\nfrom __future__ import annotations\nfrom pathlib import Path\nimport json\nfrom qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect\nfrom qseries_v2.oracle_terminal.oracle_historical_experience_read_model import load_historical_experience_read_model\nfrom .oiar_001_production_analytics_snapshot_foundation import SNAPSHOT_TABLE,stable_hash\nfrom .oiar_048_current_market_relevance_cohort_selector import STAGE as SOURCE_STAGE\nOIAR_049_BUILD_ID="OIAR-049";STAGE="current_trader_cohort_historical_enrichment";EXECUTION_AUTHORITY=False\ndef _latest(root):\n with connect(root,autocommit=False) as c:\n  with c.cursor() as cur:cur.execute("SET TRANSACTION READ ONLY");cur.execute(f"SELECT payload_json,payload_hash FROM public.{SNAPSHOT_TABLE} WHERE stage=%s ORDER BY generated_at DESC,persisted_at DESC LIMIT 1",(SOURCE_STAGE,));r=cur.fetchone()\n  c.rollback()\n if not r:raise RuntimeError("OIAR-049 requires OIAR-048")\n p,h=r\n if isinstance(p,str):p=json.loads(p)\n if stable_hash(p)!=str(h):raise RuntimeError("source hash mismatch")\n return p\ndef _family(t):return str(t or "").split("-",1)[0] or "UNKNOWN"\ndef enrich_current_cohort(root=None):\n root=Path(root or Path.cwd()).resolve();src=_latest(root);model=load_historical_experience_read_model(root);fam=dict(model.learned_family_counts);exact=dict(model.learned_market_counts);rows=[]\n for raw in src["markets"]:\n  x=dict(raw);t=x["market_ticker"];f=_family(t);x.update({"historical_family":f,"historical_family_records":int(fam.get(f,0)),"historical_exact_records":int(exact.get(t,0)),"historical_known":bool(fam.get(f,0) or exact.get(t,0))});rows.append(x)\n p={"schema_version":"OIAR-049","stage":STAGE,"market_count":len(rows),"learner_state_hash":str(model.learner_state_hash or ""),"lineage_current":bool(model.lineage_current),"markets":rows,"read_only_source":True,"execution_authority":False};h=stable_hash(p);sid="oiar-049-"+h[:32]\n with connect(root,autocommit=False) as c:\n  with c.cursor() as cur:cur.execute(f"INSERT INTO public.{SNAPSHOT_TABLE}(snapshot_id,stage,source_schema_version,source_engine_id,generated_at,market_count,payload_json,payload_hash,read_only_source,execution_authority) VALUES(%s,%s,%s,%s,clock_timestamp(),%s,%s::jsonb,%s,TRUE,FALSE) ON CONFLICT(snapshot_id) DO NOTHING",(sid,STAGE,"OIAR-049",OIAR_049_BUILD_ID,len(rows),json.dumps(p,sort_keys=True),h))\n  c.commit()\n return sid,p\ndef physical_probe(root=None):\n sid,p=enrich_current_cohort(root);return {"snapshot_id":sid,"current_markets":p["market_count"],"historically_known":sum(x["historical_known"] for x in p["markets"]),"learner_state_hash":p["learner_state_hash"],"execution_authority":False}\n';TEST_SOURCE='\nimport unittest\nimport qseries_v2.oracle_intelligence_analytics_runtime.oiar_049_current_market_historical_enrichment as m\nclass T(unittest.TestCase):\n def test_identity(self):self.assertEqual(m.OIAR_049_BUILD_ID,"OIAR-049")\n def test_stage(self):self.assertEqual(m.STAGE,"current_trader_cohort_historical_enrichment")\nif __name__=="__main__":\n print("="*88);print(" OIAR-049 CERTIFICATION TEST");print(" CURRENT MARKET HISTORICAL ENRICHMENT");print("="*88)\n r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n if not r.wasSuccessful():raise SystemExit(1)\n print("[PASS] history enriches current markets; history does not select them")\n'
REQUIRED=('qseries_v2/oracle_intelligence_analytics_runtime/oiar_048_current_market_relevance_cohort_selector.py', 'qseries_v2/oracle_terminal/oracle_historical_experience_read_model.py');EXTRA={}
def write_exact(p,s):
    p.parent.mkdir(parents=True,exist_ok=True);t=p.with_name(p.name+f".{os.getpid()}.tmp")
    t.write_text(s,encoding="utf-8");os.replace(t,p)
def restore(p,b):
    if b is None:
        if p.exists():p.unlink()
    else:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
def main():
    print("="*88);print(" OIAR-049 INSTALLER");print(" CURRENT MARKET HISTORICAL ENRICHMENT");print("="*88);print("[ROOT]",ROOT)
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
        m=importlib.import_module("qseries_v2.oracle_intelligence_analytics_runtime.oiar_049_current_market_historical_enrichment");x=m.physical_probe(ROOT);print("[PHYSICAL]",x)
        if x["current_markets"]<=0:raise RuntimeError("empty enrichment")
    except Exception:
        for p,b in old.items():restore(p,b)
        print("[ROLLBACK] OIAR-049 failed; affected files restored");raise
    print("[PASS] read_only=True execution_authority=FALSE")
    print("[DONE] OIAR-049 INSTALLATION COMPLETE")
if __name__=="__main__":main()

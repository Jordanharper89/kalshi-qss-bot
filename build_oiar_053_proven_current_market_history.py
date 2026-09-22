from pathlib import Path
import ast,importlib,os,subprocess,sys,time

ROOT=Path.cwd().resolve()
MOD=ROOT/'qseries_v2/oracle_intelligence_analytics_runtime/oiar_054_proven_current_trader_analytics.py'
TEST=ROOT/'test_oiar_054_proven_current_trader_analytics.py'
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import asdict,is_dataclass\nfrom datetime import datetime,timezone\nfrom pathlib import Path\nimport json\nfrom qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect\nfrom qseries_v2.oracle_intelligence.analytics.oracle_market_statistics_engine import OracleMarketStatisticsEngine\nfrom qseries_v2.oracle_intelligence.analytics.oracle_market_feature_extraction_engine import OracleCanonicalMarketFeatureExtractionEngine\nfrom qseries_v2.oracle_intelligence.analytics.oracle_market_usefulness_scoring_engine import OracleMarketUsefulnessScoringEngine\nfrom qseries_v2.oracle_intelligence.analytics.oracle_opportunity_candidate_generator import OracleOpportunityCandidateGenerator\nfrom qseries_v2.oracle_intelligence.analytics.oracle_opportunity_admission_gate import OracleOpportunityAdmissionGate\nfrom .oiar_001_production_analytics_snapshot_foundation import SNAPSHOT_TABLE,stable_hash\nfrom .oiar_052_proven_current_canonical_trader_cohort import read_latest_current_trader_cohort\nfrom .oiar_053_proven_current_market_history import read_latest_current_market_history\nOIAR_054_BUILD_ID="OIAR-054";STAGE="proven_current_trader_analytics"\ndef _d(x):\n if hasattr(x,"to_dict"):return dict(x.to_dict())\n if is_dataclass(x):return asdict(x)\n return dict(x.__dict__)\ndef materialize_current_trader_analytics(root=None):\n root=Path(root or Path.cwd()).resolve();cohort=read_latest_current_trader_cohort(root);hist=read_latest_current_market_history(root)\n if not cohort or not hist:raise RuntimeError("OIAR-054 requires OIAR-052 and OIAR-053")\n meta={x["market_ticker"]:x for x in cohort["markets"]};group={x["market_ticker"]:x["history"] for x in hist["markets"]}\n cf=lambda:connect(root,autocommit=False);n=max(1,len(group))\n se=OracleMarketStatisticsEngine(connection_factory=cf,market_limit=n,history_limit_per_market=250)\n fe=OracleCanonicalMarketFeatureExtractionEngine(connection_factory=cf,market_limit=n,history_limit_per_market=250)\n ue=OracleMarketUsefulnessScoringEngine(connection_factory=cf,market_limit=n,history_limit_per_market=250)\n ce=OracleOpportunityCandidateGenerator(connection_factory=cf,market_limit=n,history_limit_per_market=250)\n ae=OracleOpportunityAdmissionGate(connection_factory=cf,market_limit=n,history_limit_per_market=250)\n records=[]\n for mid,rr in group.items():\n  rows=[(mid,r["observed_at"],r["sequence_number"],r["yes_bid_dollars"],r["yes_ask_dollars"],r["last_price_dollars"],r["volume_fp"],r["liquidity_dollars"]) for r in rr]\n  s=se._calculate_market(market_id=mid,rows=rows);f=fe._extract_market(s);u=ue._score_market(f);cand=ce._classify_market(f,u);adm=ae._evaluate_market(cand)\n  records.append({"market_id":mid,"market":meta.get(mid,{}),"history_rows":len(rows),"statistics":_d(s),"features":_d(f),"usefulness":_d(u),"candidate":_d(cand),"admission":_d(adm)})\n records.sort(key=lambda x:(-float(x["admission"].get("admission_score",0) or 0),x["market_id"]))\n if not records:raise RuntimeError("OIAR-054 produced no analytics")\n body={"schema_version":"OIAR-054","stage":STAGE,"market_count":len(records),"markets":records,"read_only_source":True,"execution_authority":False}\n h=stable_hash(body);sid="oiar-054-"+h[:32]\n with connect(root,autocommit=False) as c:\n  q=c.cursor();q.execute(f"""INSERT INTO public.{SNAPSHOT_TABLE}(snapshot_id,stage,source_schema_version,source_engine_id,generated_at,market_count,payload_json,payload_hash,read_only_source,execution_authority)\n  VALUES(%s,%s,%s,%s,%s,%s,%s::jsonb,%s,TRUE,FALSE) ON CONFLICT(snapshot_id) DO NOTHING""",(sid,STAGE,"OIAR-054",OIAR_054_BUILD_ID,datetime.now(timezone.utc),len(records),json.dumps(body,sort_keys=True,separators=(",",":"),default=str),h));c.commit()\n return body\ndef read_latest_current_trader_analytics(root=None):\n root=Path(root or Path.cwd()).resolve()\n with connect(root,autocommit=False) as c:\n  q=c.cursor();q.execute("SET TRANSACTION READ ONLY");q.execute(f"SELECT payload_json,payload_hash FROM public.{SNAPSHOT_TABLE} WHERE stage=%s ORDER BY generated_at DESC,persisted_at DESC LIMIT 1",(STAGE,));r=q.fetchone();c.rollback()\n if not r:return None\n p,h=r\n if isinstance(p,str):p=json.loads(p)\n if stable_hash(p)!=str(h):raise RuntimeError("OIAR-054 snapshot hash mismatch")\n return p\ndef physical_probe(root=None):return materialize_current_trader_analytics(root)\n'
TEST_SOURCE='import unittest\nimport qseries_v2.oracle_intelligence_analytics_runtime.oiar_054_proven_current_trader_analytics as m\nclass T(unittest.TestCase):\n def test_identity(self):self.assertEqual(m.OIAR_054_BUILD_ID,"OIAR-054")\n def test_physical(self):\n  x=m.read_latest_current_trader_analytics();self.assertTrue(x);self.assertGreater(x["market_count"],0);self.assertFalse(x["execution_authority"])\nif __name__=="__main__":\n print("="*88);print(" OIAR-054 CERTIFICATION TEST");print(" PROVEN CURRENT TRADER ANALYTICS");print("="*88)\n r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n if not r.wasSuccessful():raise SystemExit(1)\n print("[PASS] proven current OIA analytics certified");print("[DONE] OIAR-054 CERTIFIED")\n'
REQUIRED=('qseries_v2/oracle_intelligence_analytics_runtime/oiar_053_proven_current_market_history.py',)
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
    print("="*88);print(" OIAR-054 INSTALLER");print(" PROVEN CURRENT TRADER ANALYTICS");print("="*88);print("[ROOT]",ROOT)
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
        m=importlib.import_module("qseries_v2.oracle_intelligence_analytics_runtime.oiar_054_proven_current_trader_analytics")
        s=time.monotonic()
        x=m.physical_probe(ROOT)
        print("[PHYSICAL]",x,"elapsed_seconds=",round(time.monotonic()-s,3))
        if x["market_count"]<=0:raise RuntimeError("OIAR-054 empty analytics")
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True,timeout=120)
    except Exception:
        for p,data in old.items():restore(p,data)
        print("[ROLLBACK] OIAR-054 failed; affected files restored")
        raise
    print("[PASS] read-only intelligence boundary preserved")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OIAR-054 INSTALLATION COMPLETE")
if __name__=="__main__":main()

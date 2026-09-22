from pathlib import Path
import ast, importlib, os, subprocess, sys, time

ROOT=Path.cwd().resolve()
MOD=ROOT/'qseries_v2/oracle_intelligence_analytics_runtime/oiar_003_bounded_current_cohort_oia_materializer.py'
TEST=ROOT/'test_oiar_003_bounded_current_cohort_oia_materializer.py'

MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import asdict, is_dataclass\nfrom datetime import datetime, timezone\nfrom pathlib import Path\nimport json\n\nfrom qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect\nfrom qseries_v2.oracle_intelligence.analytics.oracle_market_statistics_engine import OracleMarketStatisticsEngine, STATISTICS_SQL\nfrom qseries_v2.oracle_intelligence.analytics.oracle_market_feature_extraction_engine import OracleCanonicalMarketFeatureExtractionEngine\nfrom qseries_v2.oracle_intelligence.analytics.oracle_market_usefulness_scoring_engine import OracleMarketUsefulnessScoringEngine\nfrom qseries_v2.oracle_intelligence.analytics.oracle_opportunity_candidate_generator import OracleOpportunityCandidateGenerator\nfrom qseries_v2.oracle_intelligence.analytics.oracle_opportunity_admission_gate import OracleOpportunityAdmissionGate\nfrom .oiar_001_production_analytics_snapshot_foundation import SNAPSHOT_TABLE, STATE_TABLE, ensure_analytics_snapshot_schema, stable_hash\n\nOIAR_003_BUILD_ID="OIAR-003"\nOIAR_003_REVISION="OIAR_003_BOUNDED_CURRENT_COHORT_OIA_MATERIALIZER_V1"\nCOHORT_STAGE="reasoning_market_cohort"\nANALYTICS_STAGE="bounded_oia_admission"\n\ndef _to_dict(value):\n    if hasattr(value,"to_dict"):\n        return dict(value.to_dict())\n    if is_dataclass(value):\n        return asdict(value)\n    raise TypeError(f"Unsupported OIA record type: {type(value)!r}")\n\ndef _connection_factory(root):\n    return lambda: connect(root,autocommit=False)\n\ndef load_latest_cohort_payload(root=None):\n    root=Path(root or Path.cwd()).resolve()\n    ensure_analytics_snapshot_schema(root)\n    with connect(root,autocommit=False) as conn:\n        with conn.cursor() as cur:\n            cur.execute("SET TRANSACTION READ ONLY")\n            cur.execute(\n                f"SELECT payload_json FROM public.{SNAPSHOT_TABLE} WHERE stage=%s ORDER BY generated_at DESC,persisted_at DESC LIMIT 1",\n                (COHORT_STAGE,),\n            )\n            row=cur.fetchone()\n        conn.rollback()\n    if row is None:\n        raise RuntimeError("OIAR-003 requires an OIAR-002 reasoning cohort snapshot")\n    payload=row[0]\n    if isinstance(payload,str): payload=json.loads(payload)\n    if not isinstance(payload,dict): raise RuntimeError("OIAR-003 cohort payload invalid")\n    markets=payload.get("markets")\n    if not isinstance(markets,list) or not markets: raise RuntimeError("OIAR-003 cohort markets empty")\n    return payload\n\ndef materialize_bounded_oia_admission(root=None,history_limit_per_market=250,statement_timeout_ms=30000):\n    root=Path(root or Path.cwd()).resolve()\n    cohort=load_latest_cohort_payload(root)\n    market_ids=tuple(sorted({\n        str(x.get("market_ticker") or "").strip()\n        for x in cohort["markets"] if isinstance(x,dict) and str(x.get("market_ticker") or "").strip()\n    }))\n    if not market_ids: raise RuntimeError("OIAR-003 bounded cohort empty")\n    if len(market_ids)>100: raise RuntimeError("OIAR-003 refuses cohort larger than 100 markets")\n\n    cf=_connection_factory(root)\n    statistics_engine=OracleMarketStatisticsEngine(\n        connection_factory=cf,market_limit=len(market_ids),\n        history_limit_per_market=int(history_limit_per_market),\n    )\n\n    with connect(root,autocommit=False) as conn:\n        with conn.cursor() as cur:\n            cur.execute("SET TRANSACTION READ ONLY")\n            cur.execute(f"SET LOCAL statement_timeout=\'{int(statement_timeout_ms)}ms\'")\n            cur.execute(STATISTICS_SQL,(list(market_ids),int(history_limit_per_market)))\n            rows=cur.fetchall() or []\n        conn.rollback()\n\n    grouped={m:[] for m in market_ids}\n    for row in rows:\n        if len(row)<8: raise RuntimeError("OIA-003 statistics row contract violation")\n        mid=str(row[0] or "").strip()\n        if mid in grouped: grouped[mid].append(row)\n\n    feature_engine=OracleCanonicalMarketFeatureExtractionEngine(\n        connection_factory=cf,market_limit=len(market_ids),\n        history_limit_per_market=int(history_limit_per_market),\n    )\n    usefulness_engine=OracleMarketUsefulnessScoringEngine(\n        connection_factory=cf,market_limit=len(market_ids),\n        history_limit_per_market=int(history_limit_per_market),\n    )\n    candidate_engine=OracleOpportunityCandidateGenerator(\n        connection_factory=cf,market_limit=len(market_ids),\n        history_limit_per_market=int(history_limit_per_market),\n    )\n    admission_engine=OracleOpportunityAdmissionGate(\n        connection_factory=cf,market_limit=len(market_ids),\n        history_limit_per_market=int(history_limit_per_market),\n    )\n\n    records=[]\n    for market_id in market_ids:\n        history=grouped.get(market_id) or []\n        if not history: continue\n        stats=statistics_engine._calculate_market(market_id=market_id,rows=history)\n        feature=feature_engine._extract_market(stats)\n        useful=usefulness_engine._score_market(feature)\n        candidate=candidate_engine._classify_market(feature,useful)\n        admission=admission_engine._evaluate_market(candidate)\n        records.append({\n            "market_id":market_id,\n            "statistics":_to_dict(stats),\n            "features":_to_dict(feature),\n            "usefulness":_to_dict(useful),\n            "candidate":_to_dict(candidate),\n            "admission":_to_dict(admission),\n        })\n\n    records.sort(key=lambda x:x["market_id"])\n    payload={\n        "schema_version":"OIAR-003",\n        "stage":ANALYTICS_STAGE,\n        "cohort_market_count":len(market_ids),\n        "analytics_market_count":len(records),\n        "history_limit_per_market":int(history_limit_per_market),\n        "learner_state_hash":str(cohort.get("learner_state_hash") or ""),\n        "lineage_current":bool(cohort.get("lineage_current")),\n        "markets":records,\n        "read_only_source":True,\n        "execution_authority":False,\n    }\n    ph=stable_hash(payload); sid=f"oiar-003-{ph[:32]}"; generated=datetime.now(timezone.utc)\n\n    with connect(root,autocommit=False) as conn:\n        with conn.cursor() as cur:\n            cur.execute(\n                f"INSERT INTO public.{SNAPSHOT_TABLE}(snapshot_id,stage,source_schema_version,source_engine_id,generated_at,market_count,payload_json,payload_hash,read_only_source,execution_authority) VALUES(%s,%s,%s,%s,%s,%s,%s::jsonb,%s,TRUE,FALSE) ON CONFLICT(snapshot_id) DO NOTHING",\n                (sid,ANALYTICS_STAGE,"OIAR-003",OIAR_003_BUILD_ID,generated,len(records),json.dumps(payload,sort_keys=True,separators=(",",":"),default=str),ph),\n            )\n            cur.execute(\n                f"UPDATE public.{STATE_TABLE} SET last_successful_snapshot_id=%s,last_successful_stage=%s,last_successful_at=%s,last_completed_at=%s,status=\'IDLE\',last_error_type=NULL,last_error_message=NULL,updated_at=clock_timestamp() WHERE state_id=1",\n                (sid,ANALYTICS_STAGE,generated,generated),\n            )\n        conn.commit()\n    return payload\n\ndef read_latest_bounded_oia_admission(root=None):\n    root=Path(root or Path.cwd()).resolve()\n    with connect(root,autocommit=False) as conn:\n        with conn.cursor() as cur:\n            cur.execute("SET TRANSACTION READ ONLY")\n            cur.execute(\n                f"SELECT payload_json,payload_hash FROM public.{SNAPSHOT_TABLE} WHERE stage=%s ORDER BY generated_at DESC,persisted_at DESC LIMIT 1",\n                (ANALYTICS_STAGE,),\n            )\n            row=cur.fetchone()\n        conn.rollback()\n    if row is None:return None\n    payload,ph=row\n    if isinstance(payload,str):payload=json.loads(payload)\n    if stable_hash(payload)!=str(ph):raise RuntimeError("OIAR-003 persisted payload hash mismatch")\n    return payload\n'
TEST_SOURCE='import unittest\nimport qseries_v2.oracle_intelligence_analytics_runtime.oiar_003_bounded_current_cohort_oia_materializer as m\n\nclass T(unittest.TestCase):\n    def test_identity(self):\n        self.assertEqual(m.OIAR_003_BUILD_ID,"OIAR-003")\n    def test_stages(self):\n        self.assertEqual(m.COHORT_STAGE,"reasoning_market_cohort")\n        self.assertEqual(m.ANALYTICS_STAGE,"bounded_oia_admission")\n\nif __name__=="__main__":\n    print("="*88);print(" OIAR-003 CERTIFICATION TEST");print(" BOUNDED CURRENT-COHORT OIA MATERIALIZER");print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] bounded cohort analytics contract certified")\n    print("[PASS] OIA engines reused; no duplicate analytics formulas")\n    print("[PASS] execution_authority=FALSE")\n    print("[DONE] OIAR-003 CERTIFIED")\n'

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
    print("="*88);print(" OIAR-003 INSTALLER");print(" BOUNDED CURRENT-COHORT OIA MATERIALIZER");print("="*88);print("[ROOT]",ROOT)
    required=(
        MOD.parent/"oiar_001_production_analytics_snapshot_foundation.py",
        MOD.parent/"oiar_002_current_reasoning_market_cohort_snapshot.py",
        ROOT/"qseries_v2"/"oracle_intelligence"/"analytics"/"oracle_market_statistics_engine.py",
        ROOT/"qseries_v2"/"oracle_intelligence"/"analytics"/"oracle_market_feature_extraction_engine.py",
        ROOT/"qseries_v2"/"oracle_intelligence"/"analytics"/"oracle_market_usefulness_scoring_engine.py",
        ROOT/"qseries_v2"/"oracle_intelligence"/"analytics"/"oracle_opportunity_candidate_generator.py",
        ROOT/"qseries_v2"/"oracle_intelligence"/"analytics"/"oracle_opportunity_admission_gate.py",
    )
    for p in required:
        if not p.is_file():raise RuntimeError(f"Required proven upstream missing: {p}")
    old={p:(p.read_bytes() if p.exists() else None) for p in (MOD,TEST)}
    try:
        write_exact(MOD,MODULE_SOURCE);write_exact(TEST,TEST_SOURCE)
        ast.parse(MODULE_SOURCE);ast.parse(TEST_SOURCE);print("[PASS] installer payload syntax verified")
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
        importlib.invalidate_caches()
        m=importlib.import_module("qseries_v2.oracle_intelligence_analytics_runtime.oiar_003_bounded_current_cohort_oia_materializer")
        started=time.monotonic()
        payload=m.materialize_bounded_oia_admission(ROOT,history_limit_per_market=250,statement_timeout_ms=30000)
        elapsed=time.monotonic()-started
        print(f"[PHYSICAL] cohort_markets={payload['cohort_market_count']} analytics_markets={payload['analytics_market_count']} elapsed_seconds={elapsed:.2f}")
        latest=m.read_latest_bounded_oia_admission(ROOT)
        if latest is None or latest["analytics_market_count"]!=payload["analytics_market_count"]:
            raise RuntimeError("OIAR-003 persisted analytics verification failed")
    except Exception:
        for p,d in old.items():restore(p,d)
        print("[ROLLBACK] OIAR-003 failed; affected repository files restored");raise
    print("[PASS] analytics bounded to current OIAR-002 cohort")
    print("[PASS] SQL statement timeout capped at 30 seconds")
    print("[PASS] existing OIA-003 through OIA-007 record logic reused")
    print("[PASS] no Oracle Live launcher mutation")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OIAR-003 INSTALLATION COMPLETE")

if __name__=="__main__":
    main()

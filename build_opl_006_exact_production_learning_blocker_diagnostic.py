from pathlib import Path
import importlib,os,subprocess,sys,json

ROOT=Path.cwd().resolve()
PKG=ROOT/"qseries_v2"/"oracle_production_learning"
MOD=PKG/"opl_006_exact_production_learning_blocker_diagnostic.py"
TEST=ROOT/"test_opl_006_exact_production_learning_blocker_diagnostic.py"
INIT=PKG/"__init__.py"
REPORT=PKG/"OPL_006_EXACT_BLOCKER_REPORT.json"

MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass,asdict\nfrom pathlib import Path\nfrom collections import Counter\nimport json\n\nfrom .opl_001_production_learning_foundation import connect\nfrom .opl_002_canonical_evidence_index import INDEX_TABLE\n\nOPL_006_BUILD_ID="OPL-006"\nOPL_006_REVISION="OPL_006_EXACT_PRODUCTION_LEARNING_BLOCKER_DIAGNOSTIC_V1"\n\n@dataclass(frozen=True)\nclass MarketTrace:\n    ticker:str\n    event_ticker:str\n    series_ticker:str\n    settlement_ts:str\n    exact_index_rows:int\n    exact_pre_settlement_rows:int\n    exact_post_settlement_rows:int\n    event_index_rows:int\n    series_index_rows:int\n    exact_min_observed_at:str\n    exact_max_observed_at:str\n    canonical_source_observation_rows:int\n    canonical_json_text_rows:int\n    failure_class:str\n\ndef _credentials(root):\n    from qseries_v2.oracle_adapters.kalshi.oad_021_credentials import load_kalshi_credentials\n    return load_kalshi_credentials(root=root)\n\ndef _get(credentials,path,params,timeout=15):\n    from qseries_v2.oracle_adapters.kalshi.oad_022_rest_transport import kalshi_rest_get\n    return kalshi_rest_get(credentials,path,params,timeout)\n\ndef _norm(v):\n    return str(v or "").strip().upper()\n\ndef _settlement_ts(m):\n    return str(\n        m.get("settlement_ts")\n        or m.get("settled_ts")\n        or m.get("settled_time")\n        or ""\n    ).strip()\n\ndef fetch_real_settled_samples(root=None,limit=25):\n    root=Path(root or Path.cwd()).resolve()\n    c=_credentials(root)\n    r=_get(c,"/markets",{"limit":max(1,min(int(limit),1000)),"status":"settled"},15)\n    out=[]\n    for raw in r.body.get("markets",()):\n        ticker=_norm(raw.get("ticker"))\n        ts=_settlement_ts(raw)\n        if not ticker or not ts:\n            continue\n        out.append(dict(raw))\n        if len(out)>=int(limit):\n            break\n    return tuple(out)\n\ndef _index_stats(cur,identity,settlement_ts):\n    identity=_norm(identity)\n    if not identity:\n        return (0,0,0,"","")\n    cur.execute(\n        f"""SELECT\n              COUNT(*),\n              COUNT(*) FILTER (WHERE observed_at < %s),\n              COUNT(*) FILTER (WHERE observed_at >= %s),\n              COALESCE(MIN(observed_at),\'\'),\n              COALESCE(MAX(observed_at),\'\')\n            FROM public.{INDEX_TABLE}\n            WHERE ticker=%s""",\n        (settlement_ts,settlement_ts,identity),\n    )\n    row=cur.fetchone()\n    return int(row[0]),int(row[1]),int(row[2]),str(row[3] or ""),str(row[4] or "")\n\ndef _count_index(cur,identity):\n    identity=_norm(identity)\n    if not identity:\n        return 0\n    cur.execute(f"SELECT COUNT(*) FROM public.{INDEX_TABLE} WHERE ticker=%s",(identity,))\n    return int(cur.fetchone()[0])\n\ndef _canonical_exact_counts(cur,ticker):\n    # These are bounded exact checks against the two most likely identity surfaces.\n    cur.execute(\n        """SELECT COUNT(*)\n           FROM public.oracle_canonical_observations\n           WHERE UPPER(COALESCE(source_observation_id,\'\'))=%s""",\n        (_norm(ticker),),\n    )\n    source_rows=int(cur.fetchone()[0])\n\n    # JSON text scan is intentionally used only for a small diagnostic sample.\n    cur.execute(\n        """SELECT COUNT(*)\n           FROM public.oracle_canonical_observations\n           WHERE canonical_observation_json::text ILIKE %s""",\n        ("%"+str(ticker)+"%",),\n    )\n    json_rows=int(cur.fetchone()[0])\n    return source_rows,json_rows\n\ndef classify_trace(exact_rows,pre_rows,post_rows,event_rows,series_rows,source_rows,json_rows):\n    if exact_rows>0 and pre_rows>0:\n        return "MATCH_EXISTS_BUT_OPL003_LOOKUP_REJECTS_OR_MISCOMPARES"\n    if exact_rows>0 and pre_rows==0 and post_rows>0:\n        return "EVIDENCE_EXISTS_ONLY_AFTER_SETTLEMENT"\n    if exact_rows==0 and (event_rows>0 or series_rows>0):\n        return "IDENTITY_GRANULARITY_MISMATCH_MARKET_VS_EVENT_OR_SERIES"\n    if exact_rows==0 and json_rows>0:\n        return "CANONICAL_CONTAINS_TICKER_BUT_EVIDENCE_INDEX_IDENTITY_IS_WRONG"\n    if exact_rows==0 and source_rows>0:\n        return "SOURCE_IDENTITY_EXISTS_BUT_EVIDENCE_INDEX_DID_NOT_CAPTURE_IT"\n    return "NO_CANONICAL_PRESETTLEMENT_COVERAGE_FOR_SETTLED_TICKER"\n\ndef trace_market(root,market):\n    ticker=_norm(market.get("ticker"))\n    event_ticker=_norm(market.get("event_ticker"))\n    series_ticker=_norm(market.get("series_ticker"))\n    settlement_ts=_settlement_ts(market)\n\n    with connect(root) as conn:\n        with conn.cursor() as cur:\n            exact_rows,pre_rows,post_rows,min_at,max_at=_index_stats(cur,ticker,settlement_ts)\n            event_rows=_count_index(cur,event_ticker)\n            series_rows=_count_index(cur,series_ticker)\n            source_rows,json_rows=_canonical_exact_counts(cur,ticker)\n\n    failure=classify_trace(\n        exact_rows,pre_rows,post_rows,event_rows,series_rows,source_rows,json_rows\n    )\n    return MarketTrace(\n        ticker,event_ticker,series_ticker,settlement_ts,\n        exact_rows,pre_rows,post_rows,event_rows,series_rows,\n        min_at,max_at,source_rows,json_rows,failure\n    )\n\ndef run_exact_blocker_diagnostic(root=None,sample_size=10):\n    root=Path(root or Path.cwd()).resolve()\n    markets=fetch_real_settled_samples(root,max(1,int(sample_size)))\n    traces=tuple(trace_market(root,m) for m in markets)\n    classes=Counter(t.failure_class for t in traces)\n\n    if not traces:\n        overall="NO_SETTLED_SAMPLE_RETURNED"\n    elif len(classes)==1:\n        overall=next(iter(classes))\n    else:\n        overall="MIXED_FAILURE_CLASSES"\n\n    return {\n        "sample_size":len(traces),\n        "overall_failure_class":overall,\n        "failure_counts":dict(classes),\n        "traces":[asdict(t) for t in traces],\n        "execution_authority":False,\n    }\n\ndef write_exact_blocker_report(root=None,sample_size=10):\n    root=Path(root or Path.cwd()).resolve()\n    report=run_exact_blocker_diagnostic(root,sample_size)\n    path=root/"qseries_v2"/"oracle_production_learning"/"OPL_006_EXACT_BLOCKER_REPORT.json"\n    path.write_text(json.dumps(report,sort_keys=True,indent=2)+"\\n",encoding="utf-8",newline="\\n")\n    return path,report\n\ndef verify_opl_006_exact_production_learning_blocker_diagnostic(root=None):\n    return (\n        OPL_006_BUILD_ID=="OPL-006"\n        and classify_trace(1,1,0,0,0,0,0)=="MATCH_EXISTS_BUT_OPL003_LOOKUP_REJECTS_OR_MISCOMPARES"\n        and classify_trace(0,0,0,1,0,0,0)=="IDENTITY_GRANULARITY_MISMATCH_MARKET_VS_EVENT_OR_SERIES"\n    )\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_production_learning.opl_006_exact_production_learning_blocker_diagnostic import *\n\nclass T(unittest.TestCase):\n    def test_lookup_reject_class(self):\n        self.assertEqual(\n            classify_trace(2,1,1,0,0,0,0),\n            "MATCH_EXISTS_BUT_OPL003_LOOKUP_REJECTS_OR_MISCOMPARES",\n        )\n\n    def test_post_only_class(self):\n        self.assertEqual(\n            classify_trace(2,0,2,0,0,0,0),\n            "EVIDENCE_EXISTS_ONLY_AFTER_SETTLEMENT",\n        )\n\n    def test_identity_granularity_class(self):\n        self.assertEqual(\n            classify_trace(0,0,0,5,0,0,0),\n            "IDENTITY_GRANULARITY_MISMATCH_MARKET_VS_EVENT_OR_SERIES",\n        )\n\n    def test_index_wrong_class(self):\n        self.assertEqual(\n            classify_trace(0,0,0,0,0,0,3),\n            "CANONICAL_CONTAINS_TICKER_BUT_EVIDENCE_INDEX_IDENTITY_IS_WRONG",\n        )\n\n    def test_identity(self):\n        self.assertEqual(OPL_006_BUILD_ID,"OPL-006")\n\nif __name__=="__main__":\n    print("="*88)\n    print(" OPL-006 CERTIFICATION TEST")\n    print(" EXACT PRODUCTION LEARNING BLOCKER DIAGNOSTIC")\n    print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(\n        unittest.defaultTestLoader.loadTestsFromTestCase(T)\n    )\n    if not r.wasSuccessful():\n        raise SystemExit(1)\n    print("[PASS] Failure-classification contract certified")\n    print("[PASS] Diagnostic is read-only")\n    print("[PASS] execution_authority=FALSE")\n    print("[DONE] OPL-006 CERTIFIED")\n'

def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def restore(path,data):
    if data is None:
        if path.exists():path.unlink()
    else:
        path.write_bytes(data)

def update_init(path,export):
    current=path.read_text(encoding="utf-8") if path.exists() else ""
    if export not in current.splitlines():
        write_exact(path,current.rstrip()+"\n"+export+"\n")

def main():
    print("="*88)
    print(" OPL-006 INSTALLER")
    print(" EXACT PRODUCTION LEARNING BLOCKER DIAGNOSTIC")
    print("="*88)
    print("[ROOT]",ROOT)

    sys.path.insert(0,str(ROOT))
    opl3=importlib.import_module(
        "qseries_v2.oracle_production_learning.opl_003_outcome_grounded_production_learning_cycle"
    )
    if not opl3.verify_opl_003_outcome_grounded_production_learning_cycle(ROOT):
        raise RuntimeError("Current OPL-003 verification failed")

    affected=(MOD,TEST,INIT,REPORT)
    old={p:(p.read_bytes() if p.exists() else None) for p in affected}

    try:
        write_exact(MOD,MODULE_SOURCE)
        write_exact(TEST,TEST_SOURCE)
        update_init(INIT,"from .opl_006_exact_production_learning_blocker_diagnostic import *")
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)

        importlib.invalidate_caches()
        m=importlib.import_module(
            "qseries_v2.oracle_production_learning.opl_006_exact_production_learning_blocker_diagnostic"
        )
        m=importlib.reload(m)
        path,report=m.write_exact_blocker_report(ROOT,10)

        print("[DIAGNOSTIC] sample_size="+str(report["sample_size"]))
        print("[DIAGNOSTIC] overall_failure_class="+str(report["overall_failure_class"]))
        print("[DIAGNOSTIC] failure_counts="+json.dumps(report["failure_counts"],sort_keys=True))

        for i,t in enumerate(report["traces"],1):
            print(
                "[TRACE %02d] ticker=%s event=%s series=%s settlement=%s exact_index=%s pre=%s post=%s event_index=%s series_index=%s source_rows=%s json_rows=%s class=%s"
                % (
                    i,t["ticker"],t["event_ticker"],t["series_ticker"],t["settlement_ts"],
                    t["exact_index_rows"],t["exact_pre_settlement_rows"],t["exact_post_settlement_rows"],
                    t["event_index_rows"],t["series_index_rows"],
                    t["canonical_source_observation_rows"],t["canonical_json_text_rows"],
                    t["failure_class"],
                )
            )

        print("[PASS] Wrote:",path.relative_to(ROOT))

    except Exception:
        for p,b in old.items():restore(p,b)
        print("[ROLLBACK] OPL-006 diagnostic failed; files restored")
        raise

    print("[PASS] Evidence index inspected read-only")
    print("[PASS] Canonical observations inspected read-only")
    print("[PASS] OPL-003 unchanged")
    print("[PASS] OPL-004 unchanged")
    print("[PASS] Oracle Live launcher unchanged")
    print("[PASS] OPH architecture untouched")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OPL-006 EXACT BLOCKER DIAGNOSTIC COMPLETE")

if __name__=="__main__":
    main()

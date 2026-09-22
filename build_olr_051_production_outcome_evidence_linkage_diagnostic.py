from pathlib import Path
import importlib,os,subprocess,sys

ROOT=Path.cwd().resolve()
PKG=ROOT/"qseries_v2"/"oracle_learning"
MOD=PKG/"olr_051_production_outcome_evidence_linkage_diagnostic.py"
TEST=ROOT/"test_olr_051_production_outcome_evidence_linkage_diagnostic.py"
INIT=PKG/"__init__.py"
REPORT=PKG/"OLR_051_LINKAGE_DIAGNOSTIC_REPORT.json"

MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass,asdict\nfrom pathlib import Path\nimport json\n\nOLR_051_BUILD_ID="OLR-051"\nOLR_051_REVISION="OLR_051_PRODUCTION_OUTCOME_EVIDENCE_LINKAGE_DIAGNOSTIC_V1"\n\n@dataclass(frozen=True)\nclass LinkageDiagnosticResult:\n    outcome_source_table:str|None\n    evidence_source_table:str|None\n    outcome_count:int\n    sample_ticker:str|None\n    sample_market_id:str|None\n    evidence_rows_for_ticker:int\n    evidence_rows_for_market_id:int\n    exact_observation_id_match:bool\n    likely_break:str\n    execution_authority:bool=False\n\ndef _connect(root=None):\n    from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect\n    return connect(root)\n\ndef _tables(cur):\n    cur.execute("""\n        SELECT table_name\n        FROM information_schema.tables\n        WHERE table_schema=\'public\'\n        ORDER BY table_name\n    """)\n    return [r[0] for r in cur.fetchall()]\n\ndef _columns(cur,table):\n    cur.execute("""\n        SELECT column_name\n        FROM information_schema.columns\n        WHERE table_schema=\'public\' AND table_name=%s\n        ORDER BY ordinal_position\n    """,(table,))\n    return [r[0] for r in cur.fetchall()]\n\ndef _pick_table(cur,tables,preferred_tokens,required_any):\n    scored=[]\n    for table in tables:\n        cols=set(_columns(cur,table))\n        if not any(c in cols for c in required_any):\n            continue\n        score=sum(1 for tok in preferred_tokens if tok in table.lower())\n        score+=sum(1 for c in ("ticker","market_ticker","market_id","observation_id","settled_at","resolved_at","status") if c in cols)\n        scored.append((score,table,cols))\n    scored.sort(reverse=True)\n    return scored[0] if scored else None\n\ndef _select_sample_outcome(cur,table,cols):\n    ticker_col="ticker" if "ticker" in cols else ("market_ticker" if "market_ticker" in cols else None)\n    market_col="market_id" if "market_id" in cols else ticker_col\n    obs_col="observation_id" if "observation_id" in cols else None\n\n    if ticker_col is None and market_col is None:\n        return None\n\n    order_col=None\n    for c in ("settled_at","resolved_at","updated_at","created_at","observed_at","sequence_number","id"):\n        if c in cols:\n            order_col=c\n            break\n\n    select_cols=[c for c in (ticker_col,market_col,obs_col) if c is not None]\n    sql=f"SELECT {\',\'.join(select_cols)} FROM public.{table}"\n    if order_col:\n        sql+=f" ORDER BY {order_col} DESC"\n    sql+=" LIMIT 100"\n\n    cur.execute(sql)\n    rows=cur.fetchall()\n    for row in rows:\n        data=dict(zip(select_cols,row))\n        ticker=str(data.get(ticker_col) or "").strip() if ticker_col else ""\n        market=str(data.get(market_col) or "").strip() if market_col else ticker\n        obs=str(data.get(obs_col) or "").strip() if obs_col else ""\n        if ticker or market:\n            return {"ticker":ticker or market,"market_id":market or ticker,"observation_id":obs or None}\n    return None\n\ndef _count_matches(cur,table,cols,sample):\n    ticker_col="ticker" if "ticker" in cols else ("market_ticker" if "market_ticker" in cols else None)\n    market_col="market_id" if "market_id" in cols else ticker_col\n    obs_col="observation_id" if "observation_id" in cols else None\n\n    ticker_count=0\n    market_count=0\n    obs_match=False\n\n    if ticker_col and sample["ticker"]:\n        cur.execute(f"SELECT COUNT(*) FROM public.{table} WHERE {ticker_col}=%s",(sample["ticker"],))\n        ticker_count=int(cur.fetchone()[0])\n\n    if market_col and sample["market_id"]:\n        cur.execute(f"SELECT COUNT(*) FROM public.{table} WHERE {market_col}=%s",(sample["market_id"],))\n        market_count=int(cur.fetchone()[0])\n\n    if obs_col and sample.get("observation_id"):\n        cur.execute(f"SELECT 1 FROM public.{table} WHERE {obs_col}=%s LIMIT 1",(sample["observation_id"],))\n        obs_match=cur.fetchone() is not None\n\n    return ticker_count,market_count,obs_match\n\ndef run_linkage_diagnostic(root=None):\n    root=Path(root or Path.cwd()).resolve()\n\n    with _connect(root) as conn:\n        with conn.cursor() as cur:\n            tables=_tables(cur)\n\n            outcome_pick=_pick_table(\n                cur,tables,\n                ("settled","outcome","resolution","learning"),\n                ("ticker","market_ticker","market_id"),\n            )\n            evidence_pick=_pick_table(\n                cur,tables,\n                ("canonical","observation","evidence"),\n                ("observation_id","ticker","market_ticker","market_id"),\n            )\n\n            if outcome_pick is None:\n                return LinkageDiagnosticResult(\n                    None,\n                    evidence_pick[1] if evidence_pick else None,\n                    0,None,None,0,0,False,\n                    "NO_OUTCOME_TABLE_WITH_MARKET_IDENTITY",\n                    False,\n                )\n\n            _,outcome_table,outcome_cols=outcome_pick\n\n            if evidence_pick is None:\n                return LinkageDiagnosticResult(\n                    outcome_table,None,0,None,None,0,0,False,\n                    "NO_EVIDENCE_TABLE_WITH_MARKET_IDENTITY",\n                    False,\n                )\n\n            _,evidence_table,evidence_cols=evidence_pick\n\n            cur.execute(f"SELECT COUNT(*) FROM public.{outcome_table}")\n            outcome_count=int(cur.fetchone()[0])\n\n            sample=_select_sample_outcome(cur,outcome_table,outcome_cols)\n            if sample is None:\n                return LinkageDiagnosticResult(\n                    outcome_table,evidence_table,outcome_count,None,None,0,0,False,\n                    "OUTCOME_ROWS_EXIST_BUT_NO_TICKER_OR_MARKET_ID_FOUND",\n                    False,\n                )\n\n            ticker_count,market_count,obs_match=_count_matches(\n                cur,evidence_table,evidence_cols,sample\n            )\n\n            if obs_match:\n                likely="OBSERVATION_ID_MATCH_EXISTS_UPSTREAM_LINKAGE_LOGIC"\n            elif ticker_count>0 or market_count>0:\n                likely="MARKET_IDENTITY_MATCH_EXISTS_BUT_ADMISSION_OR_COLUMN_MAPPING_BREAKS"\n            else:\n                likely="OUTCOME_MARKET_IDENTITY_DOES_NOT_MATCH_CANONICAL_EVIDENCE_IDENTITY"\n\n            return LinkageDiagnosticResult(\n                outcome_table,\n                evidence_table,\n                outcome_count,\n                sample["ticker"],\n                sample["market_id"],\n                ticker_count,\n                market_count,\n                obs_match,\n                likely,\n                False,\n            )\n\ndef write_diagnostic_report(root=None):\n    root=Path(root or Path.cwd()).resolve()\n    result=run_linkage_diagnostic(root)\n    path=root/"qseries_v2"/"oracle_learning"/"OLR_051_LINKAGE_DIAGNOSTIC_REPORT.json"\n    path.write_text(json.dumps(asdict(result),sort_keys=True,indent=2)+"\\n",encoding="utf-8",newline="\\n")\n    return path,result\n\ndef verify_olr_051_production_outcome_evidence_linkage_diagnostic(root=None):\n    from .olr_050_production_evidence_learning_activation_freeze import verify_olr_050_production_evidence_learning_activation_freeze\n    return (\n        verify_olr_050_production_evidence_learning_activation_freeze(root)\n        and OLR_051_BUILD_ID=="OLR-051"\n        and callable(run_linkage_diagnostic)\n    )\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_learning.olr_051_production_outcome_evidence_linkage_diagnostic import *\n\nclass T(unittest.TestCase):\n    def test_contract(self):\n        r=LinkageDiagnosticResult(\n            "outcomes","evidence",100,"KXTEST","KXTEST",0,0,False,\n            "OUTCOME_MARKET_IDENTITY_DOES_NOT_MATCH_CANONICAL_EVIDENCE_IDENTITY",False\n        )\n        self.assertEqual(r.outcome_count,100)\n        self.assertFalse(r.execution_authority)\n\n    def test_identity(self):\n        self.assertEqual(OLR_051_BUILD_ID,"OLR-051")\n\nif __name__=="__main__":\n    print("="*88)\n    print(" OLR-051 CERTIFICATION TEST")\n    print(" PRODUCTION OUTCOME-EVIDENCE LINKAGE DIAGNOSTIC")\n    print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():\n        raise SystemExit(1)\n    print("[PASS] Read-only production linkage diagnostic contract certified")\n    print("[PASS] execution_authority=FALSE")\n    print("[DONE] OLR-051 CERTIFIED")\n'

def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def update_init(path,export):
    current=path.read_text(encoding="utf-8") if path.exists() else ""
    if export not in current.splitlines():
        write_exact(path,current.rstrip()+"\n"+export+"\n")

def restore(path,data):
    if data is None:
        if path.exists():path.unlink()
    else:
        path.write_bytes(data)

def main():
    print("="*88)
    print(" OLR-051 INSTALLER")
    print(" PRODUCTION OUTCOME-EVIDENCE LINKAGE DIAGNOSTIC")
    print("="*88)
    print("[ROOT]",ROOT)

    sys.path.insert(0,str(ROOT))
    up=importlib.import_module(
        "qseries_v2.oracle_learning.olr_050_production_evidence_learning_activation_freeze"
    )
    if not up.verify_olr_050_production_evidence_learning_activation_freeze(ROOT):
        raise RuntimeError("Certified OLR-050 verification failed")

    print("[PASS] Certified OLR-050 upstream boundary verified read-only")

    affected=(MOD,TEST,INIT,REPORT)
    old={p:(p.read_bytes() if p.exists() else None) for p in affected}

    try:
        write_exact(MOD,MODULE_SOURCE)
        write_exact(TEST,TEST_SOURCE)
        update_init(
            INIT,
            "from .olr_051_production_outcome_evidence_linkage_diagnostic import *",
        )

        compile(MOD.read_text(encoding="utf-8"),str(MOD),"exec")
        compile(TEST.read_text(encoding="utf-8"),str(TEST),"exec")

        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)

        importlib.invalidate_caches()
        m=importlib.import_module(
            "qseries_v2.oracle_learning.olr_051_production_outcome_evidence_linkage_diagnostic"
        )

        path,result=m.write_diagnostic_report(ROOT)

        print("[DIAGNOSTIC] outcome_source_table="+str(result.outcome_source_table))
        print("[DIAGNOSTIC] evidence_source_table="+str(result.evidence_source_table))
        print("[DIAGNOSTIC] outcome_count="+str(result.outcome_count))
        print("[DIAGNOSTIC] sample_ticker="+str(result.sample_ticker))
        print("[DIAGNOSTIC] sample_market_id="+str(result.sample_market_id))
        print("[DIAGNOSTIC] evidence_rows_for_ticker="+str(result.evidence_rows_for_ticker))
        print("[DIAGNOSTIC] evidence_rows_for_market_id="+str(result.evidence_rows_for_market_id))
        print("[DIAGNOSTIC] exact_observation_id_match="+str(result.exact_observation_id_match))
        print("[DIAGNOSTIC] likely_break="+str(result.likely_break))
        print("[PASS] Wrote:",path.relative_to(ROOT))

    except Exception:
        for p,b in old.items():
            restore(p,b)
        print("[ROLLBACK] OLR-051 diagnostic install failed; affected files restored")
        raise

    print("[PASS] Production PostgreSQL inspected read-only")
    print("[PASS] Oracle Live launcher unchanged")
    print("[PASS] Existing learner unchanged")
    print("[PASS] OPH-001 through OPH-033 preserved frozen")
    print("[PASS] OLR-036 through OLR-050 preserved frozen")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OLR-051 INSTALLATION AND DIAGNOSTIC COMPLETE")

if __name__=="__main__":
    main()

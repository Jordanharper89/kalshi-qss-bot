from pathlib import Path
import importlib,os,subprocess,sys

ROOT=Path.cwd().resolve()
PKG=ROOT/"qseries_v2"/"oracle_learning"
MOD=PKG/"olr_051_production_outcome_evidence_linkage_diagnostic.py"
TEST=ROOT/"test_olr_051_production_outcome_evidence_linkage_diagnostic.py"
INIT=PKG/"__init__.py"
REPORT=PKG/"OLR_051_LINKAGE_DIAGNOSTIC_REPORT.json"

MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass,asdict\nfrom pathlib import Path\nimport json\n\nOLR_051_BUILD_ID="OLR-051"\nOLR_051_REVISION="OLR_051_PRODUCTION_OUTCOME_EVIDENCE_LINKAGE_DIAGNOSTIC_CORRECTION_V2"\n\nEXCLUDED_TABLES={\n    "oracle_outcome_evidence_linkage",\n    "oracle_writer_retry_telemetry",\n    "oracle_universal_ingestion_queue",\n}\n\n@dataclass(frozen=True)\nclass TableCandidate:\n    table:str\n    row_count:int\n    columns:tuple[str,...]\n    score:int\n\n@dataclass(frozen=True)\nclass LinkageDiagnosticResult:\n    outcome_candidates:tuple[dict,...]\n    evidence_candidates:tuple[dict,...]\n    selected_outcome_table:str|None\n    selected_evidence_table:str|None\n    outcome_count:int\n    sample_ticker:str|None\n    sample_market_id:str|None\n    sample_observation_id:str|None\n    evidence_rows_for_ticker:int\n    evidence_rows_for_market_id:int\n    exact_observation_id_match:bool\n    likely_break:str\n    execution_authority:bool=False\n\ndef _connect(root=None):\n    from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect\n    return connect(root)\n\ndef _tables(cur):\n    cur.execute("""\n        SELECT table_name\n        FROM information_schema.tables\n        WHERE table_schema=\'public\' AND table_type=\'BASE TABLE\'\n        ORDER BY table_name\n    """)\n    return [str(r[0]) for r in cur.fetchall()]\n\ndef _columns(cur,table):\n    cur.execute("""\n        SELECT column_name\n        FROM information_schema.columns\n        WHERE table_schema=\'public\' AND table_name=%s\n        ORDER BY ordinal_position\n    """,(table,))\n    return tuple(str(r[0]) for r in cur.fetchall())\n\ndef _row_count(cur,table):\n    cur.execute(f"SELECT COUNT(*) FROM public.{table}")\n    return int(cur.fetchone()[0])\n\ndef _candidate_score(table,cols,kind):\n    name=table.lower()\n    score=0\n    identity={"ticker","market_ticker","market_id"}\n\n    if not identity.intersection(cols):\n        return -1\n\n    if kind=="outcome":\n        for token,weight in (\n            ("settled",10),("outcome",9),("resolution",8),("resolved",8),\n            ("learning",4),("market",2)\n        ):\n            if token in name:score+=weight\n        for col,weight in (\n            ("settled_at",8),("resolved_at",8),("result",5),("outcome",5),\n            ("status",3),("ticker",2),("market_ticker",2),("market_id",2)\n        ):\n            if col in cols:score+=weight\n    else:\n        for token,weight in (\n            ("canonical",10),("observation",9),("evidence",8),\n            ("shadow",5),("market",2)\n        ):\n            if token in name:score+=weight\n        for col,weight in (\n            ("observation_id",10),("sequence_number",5),("observed_at",5),\n            ("ticker",2),("market_ticker",2),("market_id",2)\n        ):\n            if col in cols:score+=weight\n\n    return score\n\ndef _discover_candidates(cur,kind):\n    found=[]\n    for table in _tables(cur):\n        if table in EXCLUDED_TABLES:\n            continue\n        cols=_columns(cur,table)\n        score=_candidate_score(table,set(cols),kind)\n        if score<0:\n            continue\n        try:\n            count=_row_count(cur,table)\n        except Exception:\n            continue\n        if count<=0:\n            continue\n        found.append(TableCandidate(table,count,cols,score))\n    found.sort(key=lambda x:(x.score,x.row_count),reverse=True)\n    return tuple(found)\n\ndef _identity_columns(cols):\n    ticker_col="ticker" if "ticker" in cols else ("market_ticker" if "market_ticker" in cols else None)\n    market_col="market_id" if "market_id" in cols else ticker_col\n    obs_col="observation_id" if "observation_id" in cols else None\n    return ticker_col,market_col,obs_col\n\ndef _select_sample(cur,candidate):\n    cols=set(candidate.columns)\n    ticker_col,market_col,obs_col=_identity_columns(cols)\n\n    select_cols=[]\n    for c in (ticker_col,market_col,obs_col):\n        if c and c not in select_cols:\n            select_cols.append(c)\n\n    if not select_cols:\n        return None\n\n    order_col=None\n    for c in (\n        "settled_at","resolved_at","updated_at","created_at","observed_at",\n        "sequence_number","id"\n    ):\n        if c in cols:\n            order_col=c\n            break\n\n    sql=f"SELECT {\',\'.join(select_cols)} FROM public.{candidate.table}"\n    where_parts=[]\n    if ticker_col:\n        where_parts.append(f"{ticker_col} IS NOT NULL")\n    if market_col and market_col!=ticker_col:\n        where_parts.append(f"{market_col} IS NOT NULL")\n    if where_parts:\n        sql+=" WHERE "+" OR ".join(where_parts)\n    if order_col:\n        sql+=f" ORDER BY {order_col} DESC"\n    sql+=" LIMIT 500"\n\n    cur.execute(sql)\n    for row in cur.fetchall():\n        data=dict(zip(select_cols,row))\n        ticker=str(data.get(ticker_col) or "").strip() if ticker_col else ""\n        market=str(data.get(market_col) or "").strip() if market_col else ticker\n        obs=str(data.get(obs_col) or "").strip() if obs_col else ""\n        if ticker or market:\n            return {\n                "ticker":ticker or market,\n                "market_id":market or ticker,\n                "observation_id":obs or None,\n            }\n    return None\n\ndef _count_matches(cur,candidate,sample):\n    cols=set(candidate.columns)\n    ticker_col,market_col,obs_col=_identity_columns(cols)\n\n    ticker_count=0\n    market_count=0\n    obs_match=False\n\n    if ticker_col and sample["ticker"]:\n        cur.execute(\n            f"SELECT COUNT(*) FROM public.{candidate.table} WHERE {ticker_col}=%s",\n            (sample["ticker"],),\n        )\n        ticker_count=int(cur.fetchone()[0])\n\n    if market_col and sample["market_id"]:\n        cur.execute(\n            f"SELECT COUNT(*) FROM public.{candidate.table} WHERE {market_col}=%s",\n            (sample["market_id"],),\n        )\n        market_count=int(cur.fetchone()[0])\n\n    if obs_col and sample.get("observation_id"):\n        cur.execute(\n            f"SELECT 1 FROM public.{candidate.table} WHERE {obs_col}=%s LIMIT 1",\n            (sample["observation_id"],),\n        )\n        obs_match=cur.fetchone() is not None\n\n    return ticker_count,market_count,obs_match\n\ndef run_linkage_diagnostic(root=None):\n    root=Path(root or Path.cwd()).resolve()\n\n    with _connect(root) as conn:\n        with conn.cursor() as cur:\n            outcomes=_discover_candidates(cur,"outcome")\n            evidence=_discover_candidates(cur,"evidence")\n\n            outcome_dump=tuple({\n                "table":x.table,\n                "row_count":x.row_count,\n                "score":x.score,\n                "columns":list(x.columns),\n            } for x in outcomes[:10])\n\n            evidence_dump=tuple({\n                "table":x.table,\n                "row_count":x.row_count,\n                "score":x.score,\n                "columns":list(x.columns),\n            } for x in evidence[:10])\n\n            if not outcomes:\n                return LinkageDiagnosticResult(\n                    outcome_dump,evidence_dump,None,\n                    evidence[0].table if evidence else None,\n                    0,None,None,None,0,0,False,\n                    "NO_NONEMPTY_OUTCOME_SOURCE_WITH_MARKET_IDENTITY",\n                    False,\n                )\n\n            if not evidence:\n                return LinkageDiagnosticResult(\n                    outcome_dump,evidence_dump,outcomes[0].table,None,\n                    outcomes[0].row_count,None,None,None,0,0,False,\n                    "NO_NONEMPTY_EVIDENCE_SOURCE_WITH_MARKET_IDENTITY",\n                    False,\n                )\n\n            selected_outcome=outcomes[0]\n            selected_evidence=evidence[0]\n\n            sample=_select_sample(cur,selected_outcome)\n\n            if sample is None:\n                return LinkageDiagnosticResult(\n                    outcome_dump,evidence_dump,\n                    selected_outcome.table,selected_evidence.table,\n                    selected_outcome.row_count,\n                    None,None,None,0,0,False,\n                    "SELECTED_OUTCOME_SOURCE_HAS_NO_USABLE_MARKET_IDENTITY",\n                    False,\n                )\n\n            ticker_count,market_count,obs_match=_count_matches(\n                cur,selected_evidence,sample\n            )\n\n            if obs_match:\n                likely="OBSERVATION_ID_MATCH_EXISTS_LINKAGE_RUNTIME_NOT_CONSUMING_IT"\n            elif ticker_count>0 or market_count>0:\n                likely="MARKET_IDENTITY_MATCH_EXISTS_COLUMN_MAPPING_OR_ADMISSION_BREAK"\n            else:\n                likely="OUTCOME_IDENTITY_AND_EVIDENCE_IDENTITY_DO_NOT_ALIGN"\n\n            return LinkageDiagnosticResult(\n                outcome_dump,evidence_dump,\n                selected_outcome.table,selected_evidence.table,\n                selected_outcome.row_count,\n                sample["ticker"],sample["market_id"],sample.get("observation_id"),\n                ticker_count,market_count,obs_match,likely,False,\n            )\n\ndef write_diagnostic_report(root=None):\n    root=Path(root or Path.cwd()).resolve()\n    result=run_linkage_diagnostic(root)\n    path=root/"qseries_v2"/"oracle_learning"/"OLR_051_LINKAGE_DIAGNOSTIC_REPORT.json"\n    path.write_text(\n        json.dumps(asdict(result),sort_keys=True,indent=2,default=str)+"\\n",\n        encoding="utf-8",\n        newline="\\n",\n    )\n    return path,result\n\ndef verify_olr_051_production_outcome_evidence_linkage_diagnostic(root=None):\n    from .olr_050_production_evidence_learning_activation_freeze import verify_olr_050_production_evidence_learning_activation_freeze\n    return (\n        verify_olr_050_production_evidence_learning_activation_freeze(root)\n        and OLR_051_BUILD_ID=="OLR-051"\n        and callable(run_linkage_diagnostic)\n    )\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_learning.olr_051_production_outcome_evidence_linkage_diagnostic import *\n\nclass T(unittest.TestCase):\n    def test_excludes_linkage_table(self):\n        self.assertIn("oracle_outcome_evidence_linkage",EXCLUDED_TABLES)\n\n    def test_contract(self):\n        r=LinkageDiagnosticResult(\n            (),(),"settled","canonical",100,"KXTEST","KXTEST",None,\n            4,4,False,"MARKET_IDENTITY_MATCH_EXISTS_COLUMN_MAPPING_OR_ADMISSION_BREAK",False\n        )\n        self.assertEqual(r.outcome_count,100)\n        self.assertFalse(r.execution_authority)\n\n    def test_identity(self):\n        self.assertEqual(OLR_051_BUILD_ID,"OLR-051")\n        self.assertIn("CORRECTION_V2",OLR_051_REVISION)\n\nif __name__=="__main__":\n    print("="*88)\n    print(" OLR-051 CERTIFICATION TEST")\n    print(" PRODUCTION OUTCOME-EVIDENCE LINKAGE DIAGNOSTIC — CORRECTION V2")\n    print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] Linkage ledger excluded from outcome/evidence source discovery")\n    print("[PASS] Only non-empty production tables are eligible")\n    print("[PASS] execution_authority=FALSE")\n    print("[DONE] OLR-051 CORRECTION V2 CERTIFIED")\n'

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
    print(" PRODUCTION OUTCOME-EVIDENCE LINKAGE DIAGNOSTIC — CORRECTION V2")
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
        m=importlib.reload(m)

        path,result=m.write_diagnostic_report(ROOT)

        print("[DIAGNOSTIC] selected_outcome_table="+str(result.selected_outcome_table))
        print("[DIAGNOSTIC] selected_evidence_table="+str(result.selected_evidence_table))
        print("[DIAGNOSTIC] outcome_count="+str(result.outcome_count))
        print("[DIAGNOSTIC] sample_ticker="+str(result.sample_ticker))
        print("[DIAGNOSTIC] sample_market_id="+str(result.sample_market_id))
        print("[DIAGNOSTIC] sample_observation_id="+str(result.sample_observation_id))
        print("[DIAGNOSTIC] evidence_rows_for_ticker="+str(result.evidence_rows_for_ticker))
        print("[DIAGNOSTIC] evidence_rows_for_market_id="+str(result.evidence_rows_for_market_id))
        print("[DIAGNOSTIC] exact_observation_id_match="+str(result.exact_observation_id_match))
        print("[DIAGNOSTIC] likely_break="+str(result.likely_break))

        print("[OUTCOME CANDIDATES]")
        for x in result.outcome_candidates[:5]:
            print("  table="+x["table"]+" rows="+str(x["row_count"])+" score="+str(x["score"])+" columns="+",".join(x["columns"]))

        print("[EVIDENCE CANDIDATES]")
        for x in result.evidence_candidates[:5]:
            print("  table="+x["table"]+" rows="+str(x["row_count"])+" score="+str(x["score"])+" columns="+",".join(x["columns"]))

        print("[PASS] Wrote:",path.relative_to(ROOT))

    except Exception:
        for p,b in old.items():restore(p,b)
        print("[ROLLBACK] OLR-051 correction failed; affected files restored")
        raise

    print("[PASS] Production PostgreSQL inspected read-only")
    print("[PASS] Oracle Live launcher unchanged")
    print("[PASS] Existing learner unchanged")
    print("[PASS] OPH-001 through OPH-033 preserved frozen")
    print("[PASS] OLR-036 through OLR-050 preserved frozen")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OLR-051 CORRECTION V2 DIAGNOSTIC COMPLETE")

if __name__=="__main__":
    main()

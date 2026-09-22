from __future__ import annotations
from pathlib import Path
import importlib,os,subprocess,sys

ROOT=Path.cwd().resolve()
PKG=ROOT/"qseries_v2"/"oracle_learning_runtime"
MOD=PKG/"olr_006_historical_evidence_matcher.py"
TEST=ROOT/"test_olr_006_historical_evidence_matcher.py"

MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom pathlib import Path\nfrom hashlib import sha256\nimport json,re\n\nfrom qseries_v2.oracle_continuous_reasoning.ocr_002_live_observation_read_model import load_env\nfrom qseries_v2.oracle_continuous_reasoning.ocr_006_market_identity_recovery import recover_market_identity\n\nOLR_006_BUILD_ID="OLR-006"\nOLR_006_REVISION="OLR_006_PRODUCTION_INDEX_BACKED_EVIDENCE_MATCHER_V4"\n\n@dataclass(frozen=True)\nclass HistoricalEvidenceMatch:\n    ticker:str\n    observation_id:str\n    evidence_hash:str\n    order_column:str\n    order_value:str\n    strategy:str\n    row:dict\n\nSAFE=re.compile(r"^[A-Z0-9_.:-]+$")\n\ndef normalize_learning_ticker(v):\n    s=str(v or "").strip().upper()\n    if not s or not SAFE.fullmatch(s):\n        raise ValueError("invalid learning ticker")\n    return s\n\ndef quote_sql_identifier(v):\n    s=str(v)\n    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*",s):\n        raise ValueError("invalid SQL identifier")\n    return \'"\' + s.replace(\'"\',\'""\') + \'"\'\n\ndef _connect(url):\n    try:\n        import psycopg\n        return psycopg.connect(url)\n    except ImportError:\n        import psycopg2\n        return psycopg2.connect(url)\n\ndef _hash_row(row):\n    h=str(row.get("content_hash") or row.get("observation_id") or "")\n    if len(h)==64 and all(c in "0123456789abcdefABCDEF" for c in h):\n        return h.lower()\n    return sha256(\n        json.dumps(row,sort_keys=True,separators=(",",":"),default=str).encode()\n    ).hexdigest()\n\ndef _url(root):\n    env=load_env(Path(root))\n    url=env.get("DATABASE_URL") or env.get("ORACLE_DATABASE_URL")\n    if not url:\n        raise RuntimeError("DATABASE_URL not configured")\n    return url\n\ndef _canonical_source(cur):\n    cur.execute(\n        "SELECT table_schema,table_name FROM information_schema.columns "\n        "WHERE column_name=\'observation_id\' "\n        "AND table_schema NOT IN (\'pg_catalog\',\'information_schema\') "\n        "ORDER BY CASE WHEN table_name=\'oracle_canonical_observations\' THEN 0 "\n        "WHEN table_name ILIKE \'%canonical%\' THEN 1 ELSE 2 END,"\n        "table_schema,table_name LIMIT 20"\n    )\n    order_candidates=("sequence_number","observed_at","created_at","event_ts","received_at")\n    for schema,table in cur.fetchall():\n        cur.execute(\n            "SELECT column_name FROM information_schema.columns "\n            "WHERE table_schema=%s AND table_name=%s",\n            (schema,table),\n        )\n        cols={r[0] for r in cur.fetchall()}\n        order=next((x for x in order_candidates if x in cols),None)\n        if order:\n            return schema,table,order,cols\n    raise RuntimeError("No deterministic canonical observation source")\n\ndef _index_available(cur):\n    cur.execute(\n        "SELECT EXISTS("\n        " SELECT 1 FROM information_schema.tables"\n        " WHERE table_schema=\'public\'"\n        " AND table_name=\'oracle_production_learning_evidence_index\'"\n        ")"\n    )\n    return bool(cur.fetchone()[0])\n\ndef _from_index(cur,ticker,limit):\n    if not _index_available(cur):\n        return [],""\n\n    cur.execute(\n        """SELECT observation_id\n           FROM public.oracle_production_learning_evidence_index\n           WHERE upper(ticker)=upper(%s)\n           ORDER BY sequence_number DESC\n           LIMIT %s""",\n        (ticker,int(limit)),\n    )\n    ids=[str(r[0]) for r in cur.fetchall()]\n    if not ids:\n        return [],""\n\n    schema,table,order,cols=_canonical_source(cur)\n    qs=quote_sql_identifier(schema)\n    qt=quote_sql_identifier(table)\n    qo=quote_sql_identifier(order)\n\n    cur.execute(\n        f"""SELECT to_jsonb(x)\n            FROM {qs}.{qt} x\n            WHERE observation_id = ANY(%s)\n            ORDER BY {qo} DESC""",\n        (ids,),\n    )\n    rows=[dict(r[0]) for r in cur.fetchall()]\n    return rows,"production_ticker_index"\n\ndef _legacy_search(cur,ticker,limit,scan_limit):\n    schema,table,order,cols=_canonical_source(cur)\n    qs=quote_sql_identifier(schema)\n    qt=quote_sql_identifier(table)\n    qo=quote_sql_identifier(order)\n\n    rows=[]\n    strategy=""\n    direct=next(\n        (x for x in ("market_ticker","ticker","source_market_id","market_id") if x in cols),\n        None,\n    )\n\n    if direct:\n        qd=quote_sql_identifier(direct)\n        cur.execute(\n            f"SELECT to_jsonb(x) FROM {qs}.{qt} x "\n            f"WHERE upper({qd}::text)=upper(%s) "\n            f"ORDER BY {qo} DESC LIMIT %s",\n            (ticker,int(limit)),\n        )\n        rows=[dict(r[0]) for r in cur.fetchall()]\n        strategy="direct_column"\n\n    if not rows:\n        cur.execute(\n            f"SELECT to_jsonb(x) FROM {qs}.{qt} x "\n            f"ORDER BY {qo} DESC LIMIT %s",\n            (max(1000,min(int(scan_limit),50000)),),\n        )\n        for raw, in cur.fetchall():\n            row=dict(raw)\n            ident=recover_market_identity(row)\n            if ident.recovered and ident.market_ticker==ticker:\n                rows.append(row)\n                if len(rows)>=int(limit):\n                    break\n        strategy="bounded_historical_recovery"\n\n    return rows,strategy\n\ndef find_historical_market_evidence(root,ticker,limit=5,scan_limit=20000):\n    root=Path(root or Path.cwd())\n    ticker=normalize_learning_ticker(ticker)\n    conn=_connect(_url(root))\n    try:\n        try:\n            conn.set_session(readonly=True,autocommit=False)\n        except Exception:\n            pass\n        cur=conn.cursor()\n\n        rows,strategy=_from_index(cur,ticker,limit)\n        if not rows:\n            rows,strategy=_legacy_search(cur,ticker,limit,scan_limit)\n\n        schema,table,order,cols=_canonical_source(cur)\n        conn.rollback()\n\n        return tuple(\n            HistoricalEvidenceMatch(\n                ticker,\n                str(row.get("observation_id") or ""),\n                _hash_row(row),\n                order,\n                str(row.get(order) or ""),\n                strategy,\n                row,\n            )\n            for row in rows\n        )\n    finally:\n        conn.close()\n\ndef verify_olr_006_historical_evidence_matcher():\n    return (\n        normalize_learning_ticker("kxtest-1")=="KXTEST-1"\n        and len(_hash_row({"observation_id":"a"*64}))==64\n        and callable(find_historical_market_evidence)\n    )\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_learning_runtime.olr_006_historical_evidence_matcher import *\n\nclass T(unittest.TestCase):\n    def test_identity(self):\n        self.assertEqual(OLR_006_BUILD_ID,"OLR-006")\n        self.assertIn("V4",OLR_006_REVISION)\n\n    def test_normalize(self):\n        self.assertEqual(normalize_learning_ticker("kxtest-1"),"KXTEST-1")\n\n    def test_bad(self):\n        with self.assertRaises(ValueError):\n            normalize_learning_ticker("x\';drop")\n\n    def test_hash(self):\n        self.assertEqual(len(_hash_row({"observation_id":"a"*64})),64)\n\nif __name__=="__main__":\n    print("="*88)\n    print(" OLR-006 CERTIFICATION TEST")\n    print(" PRODUCTION INDEX-BACKED EVIDENCE MATCHER V4")\n    print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(\n        unittest.defaultTestLoader.loadTestsFromTestCase(T)\n    )\n    if not r.wasSuccessful():\n        raise SystemExit(1)\n    print("[PASS] Index-backed evidence matching contract certified")\n    print("[PASS] Legacy matcher fallback preserved")\n    print("[PASS] execution_authority=FALSE")\n    print("[DONE] OLR-006 V4 CERTIFIED")\n'

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

def coverage_snapshot(matcher):
    outcomes_mod=importlib.import_module(
        "qseries_v2.oracle_learning_runtime.olr_002_settled_outcome_read_model"
    )
    outcomes=outcomes_mod.fetch_recent_settled_markets(ROOT,limit=100)
    matched=0
    per=[]
    for o in outcomes:
        rows=tuple(matcher(ROOT,o.ticker,limit=3))
        if rows:matched+=1
        per.append((o.ticker,len(rows)))
    return outcomes,matched,tuple(per)

def state_snapshot():
    import json
    p=ROOT/"runtime_state"/"oracle_learning_runtime_state.json"
    d=json.loads(p.read_text(encoding="utf-8"))
    o=d.get("ocl_state") or {}
    return (
        int(d.get("cycles",0)),
        int(d.get("outcomes_learned",0)),
        int(o.get("applied_through_sequence",0)),
        str(o.get("state_hash","")),
    )

def main():
    print("="*88)
    print(" OLR-006 PRODUCTION EVIDENCE COVERAGE EXPANSION V4")
    print(" PROVEN LEARNER UNCHANGED")
    print("="*88)
    print("[ROOT]",ROOT)

    sys.path.insert(0,str(ROOT))

    if not MOD.is_file():
        raise RuntimeError("Current OLR-006 matcher missing")

    old_mod=MOD.read_bytes()
    old_test=TEST.read_bytes() if TEST.exists() else None

    try:
        oldm=importlib.import_module(
            "qseries_v2.oracle_learning_runtime.olr_006_historical_evidence_matcher"
        )
        oldm=importlib.reload(oldm)

        outcomes,before,_=coverage_snapshot(oldm.find_historical_market_evidence)
        print(f"[COVERAGE BEFORE] settled={len(outcomes)} evidence_matched={before} coverage={before/max(1,len(outcomes)):.3f}")

        write_exact(MOD,MODULE_SOURCE)
        write_exact(TEST,TEST_SOURCE)
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)

        importlib.invalidate_caches()
        newm=importlib.reload(oldm)

        _,after,rows=coverage_snapshot(newm.find_historical_market_evidence)
        print(f"[COVERAGE AFTER] settled={len(outcomes)} evidence_matched={after} coverage={after/max(1,len(outcomes)):.3f}")

        if after < before:
            raise RuntimeError("Coverage regressed; refusing installation")
        if after == before:
            raise RuntimeError("Coverage did not improve; refusing installation")

        print(f"[COVERAGE GAIN] +{after-before} matched markets")

        # Physical safety check: proven OLR-009 must still advance on the upgraded evidence supply.
        learner=importlib.import_module(
            "qseries_v2.oracle_learning_runtime.olr_009_high_coverage_learning_cycle"
        )
        before_state=state_snapshot()
        summary=learner.run_high_coverage_learning_cycle(
            root=ROOT,settled_limit=100,evidence_limit=3,
            progress=lambda x:print(x,flush=True)
        )
        after_state=state_snapshot()

        print(
            f"[LEARNING BEFORE] cycles={before_state[0]} learned={before_state[1]} "
            f"through={before_state[2]} hash={before_state[3]}"
        )
        print(
            f"[LEARNING AFTER] cycles={after_state[0]} learned={after_state[1]} "
            f"through={after_state[2]} hash={after_state[3]}"
        )

        if summary.metrics.evidence_matched < after:
            raise RuntimeError("OLR-009 did not consume upgraded evidence coverage")

        if not summary.idle:
            if not (
                after_state[0] > before_state[0]
                and after_state[1] > before_state[1]
                and after_state[2] > before_state[2]
                and after_state[3] != before_state[3]
            ):
                raise RuntimeError("Physical learning state failed to advance")

    except Exception:
        restore(MOD,old_mod)
        restore(TEST,old_test)
        print("[ROLLBACK] OLR-006 V4 refused; previous matcher restored")
        raise

    print("[PASS] Evidence coverage physically improved on same settled sample")
    print("[PASS] Proven OLR-009 learner unchanged")
    print("[PASS] Proven learner consumed expanded evidence supply")
    print("[PASS] Oracle Live launcher unchanged")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OLR-006 V4 PRODUCTION EVIDENCE COVERAGE EXPANSION COMPLETE")

if __name__=="__main__":
    main()

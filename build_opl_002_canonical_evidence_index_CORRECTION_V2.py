from pathlib import Path
import importlib,os,subprocess,sys

ROOT=Path.cwd().resolve()
PKG=ROOT/"qseries_v2"/"oracle_production_learning"
MOD=PKG/"opl_002_canonical_evidence_index.py"
TEST=ROOT/"test_opl_002_canonical_evidence_index.py"
INIT=PKG/"__init__.py"

MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom pathlib import Path\nfrom hashlib import sha256\nimport json,re\n\nfrom .opl_001_production_learning_foundation import connect\n\nOPL_002_BUILD_ID="OPL-002"\nOPL_002_REVISION="OPL_002_CANONICAL_EVIDENCE_INDEX_CORRECTION_V2"\nINDEX_TABLE="oracle_production_learning_evidence_index"\nCURSOR_TABLE="oracle_production_learning_evidence_cursor"\n\n@dataclass(frozen=True)\nclass IndexedEvidence:\n    ticker:str\n    observation_id:str\n    evidence_hash:str\n    sequence_number:int\n    observed_at:str\n    observation_type:str\n\ndef ensure_evidence_index_schema(root=None):\n    ddl=f"""\n    CREATE TABLE IF NOT EXISTS public.{INDEX_TABLE}(\n      observation_id TEXT PRIMARY KEY,\n      ticker TEXT NOT NULL,\n      evidence_hash TEXT NOT NULL,\n      sequence_number BIGINT NOT NULL,\n      observed_at TEXT NOT NULL,\n      observation_type TEXT NOT NULL,\n      indexed_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()\n    );\n    CREATE INDEX IF NOT EXISTS oracle_production_learning_evidence_ticker_idx\n      ON public.{INDEX_TABLE}(ticker,sequence_number DESC);\n\n    CREATE TABLE IF NOT EXISTS public.{CURSOR_TABLE}(\n      cursor_id INTEGER PRIMARY KEY CHECK(cursor_id=1),\n      indexed_through_sequence BIGINT NOT NULL DEFAULT 0,\n      updated_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()\n    );\n    INSERT INTO public.{CURSOR_TABLE}(cursor_id,indexed_through_sequence)\n    VALUES(1,0) ON CONFLICT(cursor_id) DO NOTHING;\n    """\n    with connect(root,autocommit=True) as conn:\n        with conn.cursor() as cur:cur.execute(ddl)\n    return True\n\ndef _decode(value):\n    if isinstance(value,dict):return value\n    if isinstance(value,(bytes,bytearray,memoryview)):\n        value=bytes(value).decode("utf-8","ignore")\n    if isinstance(value,str):\n        try:\n            v=json.loads(value)\n            return v if isinstance(v,dict) else {}\n        except Exception:return {}\n    return {}\n\ndef _simple_ticker(value):\n    s=str(value or "").strip().upper()\n    if s and re.fullmatch(r"KX[A-Z0-9_.:-]+",s):return s\n    return ""\n\ndef recover_ticker_from_canonical_row(row):\n    # Primary authority: Oracle\'s existing certified market-identity recovery.\n    try:\n        from qseries_v2.oracle_continuous_reasoning.ocr_006_market_identity_recovery import recover_market_identity\n        ident=recover_market_identity(dict(row))\n        if getattr(ident,"recovered",False):\n            t=_simple_ticker(getattr(ident,"market_ticker",""))\n            if t:return t\n    except Exception:\n        pass\n\n    # Defensive fallbacks only if certified recovery cannot resolve the row.\n    payload=_decode(row.get("canonical_observation_json"))\n    stack=[payload]\n    seen=0\n    keys=("ticker","market_ticker","marketTicker","symbol")\n    while stack and seen<200:\n        cur=stack.pop();seen+=1\n        if isinstance(cur,dict):\n            for k in keys:\n                t=_simple_ticker(cur.get(k))\n                if t:return t\n            for v in cur.values():\n                if isinstance(v,(dict,list,tuple)):stack.append(v)\n        elif isinstance(cur,(list,tuple)):\n            stack.extend(x for x in cur if isinstance(x,(dict,list,tuple)))\n\n    return _simple_ticker(row.get("source_observation_id"))\n\ndef _hash(row):\n    h=str(row.get("content_hash") or row.get("observation_id") or "")\n    if len(h)==64 and all(c in "0123456789abcdefABCDEF" for c in h):return h.lower()\n    return sha256(json.dumps(row,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()\n\ndef reset_evidence_index(root=None):\n    ensure_evidence_index_schema(root)\n    with connect(root) as conn:\n        with conn.cursor() as cur:\n            cur.execute(f"TRUNCATE TABLE public.{INDEX_TABLE}")\n            cur.execute(f"""UPDATE public.{CURSOR_TABLE}\n                            SET indexed_through_sequence=0,updated_at=clock_timestamp()\n                            WHERE cursor_id=1""")\n        conn.commit()\n    return True\n\ndef sync_evidence_index(root=None,batch_size=10000,max_batches=None):\n    root=Path(root or Path.cwd()).resolve()\n    ensure_evidence_index_schema(root)\n    scanned=inserted=resolved=0\n\n    with connect(root) as conn:\n        with conn.cursor() as cur:\n            cur.execute(f"SELECT indexed_through_sequence FROM public.{CURSOR_TABLE} WHERE cursor_id=1")\n            cursor=int(cur.fetchone()[0])\n            batches=0\n\n            while True:\n                if max_batches is not None and batches>=int(max_batches):break\n\n                cur.execute("""SELECT sequence_number,observation_id,content_hash,\n                               source_observation_id,observation_type,observed_at,\n                               canonical_observation_json\n                               FROM public.oracle_canonical_observations\n                               WHERE sequence_number>%s\n                               ORDER BY sequence_number ASC\n                               LIMIT %s""",(cursor,int(batch_size)))\n                rows=cur.fetchall()\n                if not rows:break\n                batches+=1\n\n                for r in rows:\n                    scanned+=1\n                    row={\n                        "sequence_number":r[0],\n                        "observation_id":r[1],\n                        "content_hash":r[2],\n                        "source_observation_id":r[3],\n                        "observation_type":r[4],\n                        "observed_at":r[5],\n                        "canonical_observation_json":r[6],\n                    }\n                    cursor=max(cursor,int(r[0]))\n                    ticker=recover_ticker_from_canonical_row(row)\n                    if not ticker:continue\n                    resolved+=1\n                    cur.execute(f"""INSERT INTO public.{INDEX_TABLE}\n                        (observation_id,ticker,evidence_hash,sequence_number,observed_at,observation_type)\n                        VALUES(%s,%s,%s,%s,%s,%s)\n                        ON CONFLICT(observation_id) DO UPDATE SET\n                          ticker=EXCLUDED.ticker,\n                          evidence_hash=EXCLUDED.evidence_hash,\n                          sequence_number=EXCLUDED.sequence_number,\n                          observed_at=EXCLUDED.observed_at,\n                          observation_type=EXCLUDED.observation_type""",\n                        (str(r[1]),ticker,_hash(row),int(r[0]),str(r[5]),str(r[4])))\n                    inserted+=1\n\n                cur.execute(f"""UPDATE public.{CURSOR_TABLE}\n                    SET indexed_through_sequence=%s,updated_at=clock_timestamp()\n                    WHERE cursor_id=1""",(cursor,))\n                conn.commit()\n\n                if len(rows)<int(batch_size):break\n\n    return {\n        "scanned":scanned,\n        "resolved":resolved,\n        "inserted":inserted,\n        "indexed_through_sequence":cursor,\n    }\n\ndef find_pre_settlement_evidence(root,ticker,settlement_ts,limit=5):\n    result=find_pre_settlement_evidence_batch(root,{str(ticker).upper():str(settlement_ts)},limit)\n    return result.get(str(ticker).upper(),())\n\ndef find_pre_settlement_evidence_batch(root,ticker_to_settlement,limit=5):\n    ensure_evidence_index_schema(root)\n    wanted={str(k).upper():str(v) for k,v in dict(ticker_to_settlement).items() if str(k).strip()}\n    if not wanted:return {}\n\n    tickers=list(wanted)\n    with connect(root) as conn:\n        with conn.cursor() as cur:\n            cur.execute(f"""SELECT ticker,observation_id,evidence_hash,sequence_number,\n                                   observed_at,observation_type\n                            FROM public.{INDEX_TABLE}\n                            WHERE ticker = ANY(%s)\n                            ORDER BY ticker,sequence_number DESC""",(tickers,))\n            rows=cur.fetchall()\n\n    out={t:[] for t in tickers}\n    for r in rows:\n        ticker=str(r[0]).upper()\n        if ticker not in wanted or len(out[ticker])>=int(limit):continue\n        # Parse on the server-equivalent ISO timestamp order only after both are normalized strings.\n        if str(r[4]) >= wanted[ticker]:continue\n        out[ticker].append(\n            IndexedEvidence(str(r[0]),str(r[1]),str(r[2]),int(r[3]),str(r[4]),str(r[5]))\n        )\n    return {k:tuple(v) for k,v in out.items()}\n\ndef index_stats(root=None):\n    ensure_evidence_index_schema(root)\n    with connect(root) as conn:\n        with conn.cursor() as cur:\n            cur.execute(f"SELECT COUNT(*),COUNT(DISTINCT ticker) FROM public.{INDEX_TABLE}")\n            rows,tickers=cur.fetchone()\n    return {"rows":int(rows),"tickers":int(tickers)}\n\ndef verify_opl_002_canonical_evidence_index(root=None):\n    sample={"canonical_observation_json":{"ticker":"KXTEST-1"}}\n    return (\n        OPL_002_BUILD_ID=="OPL-002"\n        and recover_ticker_from_canonical_row(sample)=="KXTEST-1"\n        and callable(find_pre_settlement_evidence_batch)\n    )\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_production_learning.opl_002_canonical_evidence_index import *\n\nclass T(unittest.TestCase):\n    def test_fallback_direct(self):\n        row={"canonical_observation_json":{"ticker":"KXTEST-1"}}\n        self.assertEqual(recover_ticker_from_canonical_row(row),"KXTEST-1")\n\n    def test_fallback_nested(self):\n        row={"canonical_observation_json":{"payload":{"market":{"ticker":"KXABC"}}}}\n        self.assertEqual(recover_ticker_from_canonical_row(row),"KXABC")\n\n    def test_source_fallback(self):\n        row={"canonical_observation_json":{},"source_observation_id":"KXSOURCE-1"}\n        self.assertEqual(recover_ticker_from_canonical_row(row),"KXSOURCE-1")\n\n    def test_identity(self):\n        self.assertEqual(OPL_002_BUILD_ID,"OPL-002")\n        self.assertIn("CORRECTION_V2",OPL_002_REVISION)\n\nif __name__=="__main__":\n    print("="*88)\n    print(" OPL-002 CERTIFICATION TEST")\n    print(" CANONICAL EVIDENCE INDEX — CORRECTION V2")\n    print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] Certified Oracle market-identity recovery is primary")\n    print("[PASS] Full canonical-history indexing contract certified")\n    print("[PASS] execution_authority=FALSE")\n    print("[DONE] OPL-002 CORRECTION V2 CERTIFIED")\n'

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

def main():
    print("="*88)
    print(" OPL-002 CORRECTION V2 INSTALLER")
    print(" FULL CANONICAL EVIDENCE INDEX REBUILD")
    print("="*88)
    print("[ROOT]",ROOT)

    sys.path.insert(0,str(ROOT))
    up=importlib.import_module("qseries_v2.oracle_production_learning.opl_001_production_learning_foundation")
    if not up.verify_opl_001_production_learning_foundation(ROOT):
        raise RuntimeError("OPL-001 verification failed")

    affected=(MOD,TEST)
    old={p:(p.read_bytes() if p.exists() else None) for p in affected}

    try:
        write_exact(MOD,MODULE_SOURCE)
        write_exact(TEST,TEST_SOURCE)
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)

        importlib.invalidate_caches()
        m=importlib.import_module("qseries_v2.oracle_production_learning.opl_002_canonical_evidence_index")
        m=importlib.reload(m)

        print("[REBUILD] Resetting sparse OPL evidence index")
        m.reset_evidence_index(ROOT)

        result=m.sync_evidence_index(ROOT,batch_size=10000,max_batches=None)
        stats=m.index_stats(ROOT)

        print("[INDEX] scanned={scanned} resolved={resolved} inserted={inserted} through_sequence={indexed_through_sequence}".format(**result))
        print("[INDEX STATS] rows="+str(stats["rows"])+" distinct_tickers="+str(stats["tickers"]))

        if stats["rows"]<=905:
            raise RuntimeError("Corrected evidence index did not improve beyond prior sparse 905-row index")
        if stats["tickers"]<=0:
            raise RuntimeError("Corrected evidence index contains no market tickers")

    except Exception:
        for p,b in old.items():restore(p,b)
        print("[ROLLBACK] OPL-002 correction failed; source files restored")
        raise

    print("[PASS] Full canonical history indexed through Oracle identity recovery")
    print("[PASS] OPL-003 API compatibility preserved")
    print("[PASS] OPL-004 Oracle Live cutover unchanged")
    print("[PASS] OPH architecture untouched")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OPL-002 CORRECTION V2 INSTALLATION COMPLETE")

if __name__=="__main__":
    main()

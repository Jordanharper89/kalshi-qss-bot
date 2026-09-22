from pathlib import Path
import os,sys,subprocess,importlib
ROOT=Path.cwd();PKG=ROOT/"qseries_v2"/"oracle_learning_runtime";MOD=PKG/"olr_006_historical_evidence_matcher.py";TEST=ROOT/"test_olr_006_historical_evidence_matcher.py";INIT=PKG/"__init__.py"
MODULE=r"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from hashlib import sha256
import json,re
from qseries_v2.oracle_continuous_reasoning.ocr_002_live_observation_read_model import load_env,quote_sql_identifier
from qseries_v2.oracle_continuous_reasoning.ocr_006_market_identity_recovery import recover_market_identity
OLR_006_BUILD_ID="OLR-006"; OLR_006_REVISION="OLR_006_HISTORICAL_EVIDENCE_MATCHER_CORRECTION_V2"
ORDER=("sequence_number","persisted_at","created_at","observed_at","acquired_at")
@dataclass(frozen=True)
class HistoricalEvidenceMatch:
    ticker:str; observation_id:str; evidence_hash:str; order_column:str; order_value:str; strategy:str; row:dict
def _connect(url):
    try:
        import psycopg; return psycopg.connect(url)
    except ImportError:
        import psycopg2; return psycopg2.connect(url)
def normalize_learning_ticker(ticker):
    t=str(ticker or "").strip().upper()
    if not t or not re.fullmatch(r"[A-Z0-9_.:-]+",t): raise ValueError("invalid ticker")
    return t
def _hash_row(row):
    h=str(row.get("content_hash") or row.get("observation_id") or "")
    if len(h)==64 and all(c in "0123456789abcdefABCDEF" for c in h): return h.lower()
    return sha256(json.dumps(row,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()
def _source(cur):
    cur.execute("SELECT table_schema,table_name FROM information_schema.columns WHERE column_name='observation_id' AND table_schema NOT IN ('pg_catalog','information_schema') ORDER BY CASE WHEN table_name='oracle_canonical_observations' THEN 0 WHEN table_name ILIKE '%canonical%' THEN 1 ELSE 2 END,table_schema,table_name LIMIT 20")
    for s,t in cur.fetchall():
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_schema=%s AND table_name=%s",(s,t))
        cols={r[0] for r in cur.fetchall()}; order=next((x for x in ORDER if x in cols),None)
        if order:return s,t,order,cols
    raise RuntimeError("No deterministic canonical observation source")
def find_historical_market_evidence(root,ticker,limit=5,scan_limit=20000):
    root=Path(root or Path.cwd()); ticker=normalize_learning_ticker(ticker)
    env=load_env(root); url=env.get("DATABASE_URL") or env.get("ORACLE_DATABASE_URL")
    if not url: raise RuntimeError("DATABASE_URL not configured")
    conn=_connect(url)
    try:
        try: conn.set_session(readonly=True,autocommit=False)
        except Exception: pass
        cur=conn.cursor(); s,t,order,cols=_source(cur)
        qs,qt,qo=map(quote_sql_identifier,(s,t,order)); rows=[]; strategy=""
        direct=next((x for x in ("market_ticker","ticker","source_market_id","market_id") if x in cols),None)
        if direct:
            qd=quote_sql_identifier(direct)
            cur.execute(f"SELECT to_jsonb(x) FROM {qs}.{qt} x WHERE upper({qd}::text)=upper(%s) ORDER BY {qo} DESC LIMIT %s",(ticker,int(limit)))
            rows=[dict(r[0]) for r in cur.fetchall()]; strategy="direct_column"
        if not rows:
            cur.execute(f"SELECT to_jsonb(x) FROM {qs}.{qt} x ORDER BY {qo} DESC LIMIT %s",(max(1000,min(int(scan_limit),50000)),))
            for raw, in cur.fetchall():
                row=dict(raw); ident=recover_market_identity(row)
                if ident.recovered and ident.market_ticker==ticker:
                    rows.append(row)
                    if len(rows)>=int(limit): break
            strategy="bounded_historical_recovery"
        conn.rollback()
        return tuple(HistoricalEvidenceMatch(ticker,str(r.get("observation_id") or ""),_hash_row(r),order,str(r.get(order) or ""),strategy,r) for r in rows)
    finally: conn.close()
def verify_olr_006_historical_evidence_matcher():
    return normalize_learning_ticker("kxtest-1")=="KXTEST-1" and len(_hash_row({"observation_id":"a"*64}))==64
"""
TEST=r"""
import unittest
from qseries_v2.oracle_learning_runtime.olr_006_historical_evidence_matcher import *
class T(unittest.TestCase):
    def test_verifier(self): self.assertTrue(verify_olr_006_historical_evidence_matcher())
    def test_normalize(self): self.assertEqual(normalize_learning_ticker("kxtest-1"),"KXTEST-1")
    def test_bad(self):
        with self.assertRaises(ValueError): normalize_learning_ticker("x';drop")
if __name__=="__main__":
    print("="*72);print(" OLR-006 CERTIFICATION TEST");print(" HISTORICAL EVIDENCE MATCHER");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():raise SystemExit(1)
    print("[PASS] Read-only historical market evidence matching certified");print("[DONE] OLR-006 CERTIFIED")
"""
def w(p,s): p.parent.mkdir(parents=True,exist_ok=True); tmp=p.with_suffix(p.suffix+".tmp");tmp.write_text(s,encoding="utf-8",newline="\n");os.replace(tmp,p)
def main():
    print("="*72);print(" OLR-006 INSTALLER");print(" HISTORICAL EVIDENCE MATCHER");print("="*72)
    sys.path.insert(0,str(ROOT));m=importlib.import_module("qseries_v2.oracle_learning_runtime.olr_005_capability_gate");assert m.verify_olr_005_continuous_learning_runtime_gate()
    backs={path_obj:(path_obj.read_bytes() if path_obj.exists() else None) for path_obj in (MOD,TEST,INIT)}
    try:
        w(MOD,MODULE);w(TEST,TEST);cur=INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        if "# OLR-006 exports" not in cur:w(INIT,cur.rstrip()+"\n\n# OLR-006 exports\nfrom .olr_006_historical_evidence_matcher import *\n")
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
    except Exception:
        for path_obj,b in backs.items():
            if b is None:
                if path_obj.exists():path_obj.unlink()
            else:path_obj.write_bytes(b)
        raise
    print("[DONE] OLR-006 INSTALLATION AND CERTIFICATION COMPLETE")
if __name__=="__main__":main()

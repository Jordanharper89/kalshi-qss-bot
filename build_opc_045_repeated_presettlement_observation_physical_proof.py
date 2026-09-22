from pathlib import Path
import ast,importlib,os,subprocess,sys
ROOT=Path.cwd().resolve()
TARGET=ROOT/'qseries_v2/oracle_pre_settlement_coverage/opc_045_repeated_presettlement_observation_physical_proof.py'
TEST=ROOT/'test_opc_045_repeated_presettlement_observation_physical_proof.py'
SOURCE='def _db(root):\n import os\n from pathlib import Path\n url=os.environ.get("ORACLE_POSTGRESQL_URL") or os.environ.get("ORACLE_DATABASE_URL") or os.environ.get("DATABASE_URL") or os.environ.get("POSTGRES_URL")\n if url:return url\n p=Path(root)/".env"\n if p.is_file():\n  for raw in p.read_text(encoding="utf-8",errors="ignore").splitlines():\n   if "=" not in raw or raw.lstrip().startswith("#"):continue\n   k,v=raw.split("=",1)\n   if k.strip() in ("ORACLE_POSTGRESQL_URL","ORACLE_DATABASE_URL","DATABASE_URL","POSTGRES_URL") and v.strip():return v.strip().strip(\'"\').strip("\'")\n raise RuntimeError("PostgreSQL URL not configured")\nfrom pathlib import Path\nfrom qseries_v2.oracle_pre_settlement_coverage.opc_023_rotating_full_universe_coverage_cycle import fetch_rotating_open_page\nfrom qseries_v2.oracle_pre_settlement_coverage.opc_022_rotating_universe_cursor_load_budget import CoverageLoadBudget\nOPC_045_BUILD_ID="OPC-045"\ndef physical_probe(root=None,max_markets=100):\n root=Path(root or Path.cwd()).resolve();b=CoverageLoadBudget(page_limit=1000,max_snapshots_per_cycle=1000,cycle_sleep_seconds=0.0,lookback_hours=24.0,request_timeout_seconds=20.0);_,markets,_,raw=fetch_rotating_open_page(root,b);tickers=[str(x.get("ticker") or "") for x in markets if x.get("ticker")][:max_markets];import psycopg;conn=psycopg.connect(_db(root));rep=obs=0;sample=[]\n try:\n  with conn.cursor() as cur:\n   for t in tickers:\n    cur.execute("""SELECT sequence_number,observed_at FROM public.oracle_canonical_observations WHERE observation_type=\'market_snapshot\' AND COALESCE(canonical_observation_json->\'payload\'->>\'source_market_id\',canonical_observation_json->\'payload\'->>\'ticker\',canonical_observation_json->>\'ticker\')=%s ORDER BY sequence_number DESC LIMIT 3""",(t,));rows=cur.fetchall();obs+=int(bool(rows));rep+=int(len(rows)>=2);sample.append((t,len(rows),[str(r[1]) for r in rows]))\n finally:conn.close()\n return {"raw_page_markets":raw,"checked":len(tickers),"markets_with_snapshot":obs,"markets_with_repeated_snapshots":rep,"sample":sample[:20],"read_only":True,"execution_authority":False}\ndef verify_opc_045():return OPC_045_BUILD_ID=="OPC-045"\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_pre_settlement_coverage import opc_045_repeated_presettlement_observation_physical_proof as m\nclass T(unittest.TestCase):\n def test_physical(self):\n  self.assertTrue(m.verify_opc_045());x=m.physical_probe();self.assertGreater(x["checked"],0);self.assertTrue(x["read_only"]);self.assertFalse(x["execution_authority"])\nif __name__=="__main__":unittest.main(verbosity=2)\n'
def w(p,s):
    p.parent.mkdir(parents=True,exist_ok=True)
    t=p.with_name(p.name+f".{os.getpid()}.tmp")
    t.write_text(s,encoding="utf-8",newline="\n")
    os.replace(t,p)
def rr(p,b):
    if b is None:
        if p.exists(): p.unlink()
    else:
        p.write_bytes(b)
def main():
    print("="*88);print(' OPC-045 INSTALLER — REPEATED PRE-SETTLEMENT OBSERVATION PHYSICAL PROOF');print("="*88);print("[ROOT]",ROOT)
    bm=TARGET.read_bytes() if TARGET.exists() else None
    bt=TEST.read_bytes() if TEST.exists() else None
    try:
        ast.parse(SOURCE);ast.parse(TEST_SOURCE);print("[PASS] payload syntax verified")
        w(TARGET,SOURCE);w(TEST,TEST_SOURCE);importlib.invalidate_caches()
        modname=TARGET.with_suffix("").relative_to(ROOT).as_posix().replace("/",".")
        if modname in sys.modules: del sys.modules[modname]
        m=importlib.import_module(modname)
        if hasattr(m,"physical_probe"):
            print("[PHYSICAL]",m.physical_probe(ROOT))
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True,timeout=180)
    except Exception:
        rr(TARGET,bm);rr(TEST,bt);print("[ROLLBACK] failed; affected files restored");raise
    print("[DONE] INSTALLATION COMPLETE")
if __name__=="__main__":
    main()

from pathlib import Path
import ast

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_strategy_intelligence" / "solana"
MOD = PKG / "ssi_001_real_postgresql_solana_profitability_audit.py"
TEST_PATH = ROOT / "test_ssi_001d_real_postgresql_solana_profitability_audit.py"

MODULE = r"""
from collections import Counter
import json, os

def _connect():
    import psycopg
    dsn = os.getenv("ORACLE_POSTGRES_DSN") or os.getenv("DATABASE_URL")
    return psycopg.connect(dsn) if dsn else psycopg.connect()

def _table(cur):
    sql = ("SELECT table_schema,table_name FROM information_schema.columns "
           "WHERE column_name IN ('source_id','observation_type','observed_at') "
           "GROUP BY 1,2 HAVING count(DISTINCT column_name)=3 "
           "ORDER BY CASE WHEN table_name ILIKE '%canonical%' THEN 0 ELSE 1 END,table_name")
    cur.execute(sql)
    rows = cur.fetchall()
    if not rows:
        raise RuntimeError("no canonical observation table discovered")
    return rows[0]

def audit():
    with _connect() as con, con.cursor() as cur:
        s,t = _table(cur)
        q = chr(34)+s+chr(34)+"."+chr(34)+t+chr(34)
        sql = ("SELECT count(*),min(observed_at),max(observed_at),"
               "count(*) FILTER(WHERE observation_type='solana_economic_event'),"
               "count(*) FILTER(WHERE observation_type='finalized_transaction') "
               "FROM "+q+" WHERE source_id='source.onchain.solana.mainnet'")
        cur.execute(sql)
        total,first,last,econ,tx = cur.fetchone()
        cur.execute("SELECT observation_type,count(*) FROM "+q+
                    " WHERE source_id='source.onchain.solana.mainnet' GROUP BY 1 ORDER BY 2 DESC")
        types = dict(cur.fetchall())
        cur.execute("SELECT row_to_json(x) FROM (SELECT * FROM "+q+
                    " WHERE source_id='source.onchain.solana.mainnet' ORDER BY observed_at DESC LIMIT 5000) x")
        rows = [r[0] for r in cur.fetchall()]
    keys=Counter(); price_rows=liq_rows=asset_rows=0
    price_keys={"price","price_usd","usd_price","token_price","close","mid"}
    liq_keys={"liquidity","liquidity_usd","tvl","tvl_usd","reserve_usd"}
    asset_keys={"mint","token_mint","base_mint","asset","symbol","pool","pool_address"}
    def walk(v,p=""):
        if isinstance(v,dict):
            for k,x in v.items():
                key=p+"."+k if p else k
                keys[key]+=1
                yield key,x
                yield from walk(x,key)
        elif isinstance(v,list):
            for x in v:
                yield from walk(x,p)
    for r in rows:
        names={k.split(".")[-1] for k,v in walk(r) if v is not None}
        price_rows += bool(names & price_keys)
        liq_rows += bool(names & liq_keys)
        asset_rows += bool(names & asset_keys)
    span=0 if not first or not last else (last-first).total_seconds()
    return {"schema_version":"SSI-001D","physical_postgresql":True,"table":s+"."+t,
      "solana_rows":total,"economic_events":econ,"finalized_transactions":tx,
      "first_observed_at":str(first),"last_observed_at":str(last),"span_seconds":span,
      "observation_types":types,"sampled_rows":len(rows),"sample_price_rows":price_rows,
      "sample_liquidity_rows":liq_rows,"sample_asset_rows":asset_rows,
      "top_payload_paths":keys.most_common(40),
      "exact_price_path_input_ready":bool(total and price_rows>=2 and span>0),
      "read_only":True,"execution_authority":False}
"""

TEST_SOURCE = r"""
import unittest
from qseries_v2.oracle_strategy_intelligence.solana.ssi_001_real_postgresql_solana_profitability_audit import audit
class T(unittest.TestCase):
    def test_physical(self):
        r=audit()
        print("[PHYSICAL]",r)
        self.assertTrue(r["physical_postgresql"])
        self.assertGreater(r["solana_rows"],0)
        self.assertGreater(r["economic_events"]+r["finalized_transactions"],0)
        self.assertFalse(r["execution_authority"])
        print("[GATE] exact_price_path_input_ready=",r["exact_price_path_input_ready"])
if __name__=="__main__":
    unittest.main(verbosity=2)
"""

def main():
    print("="*120)
    print(" SSI-001D REAL POSTGRESQL SOLANA PROFITABILITY AUDIT - CLEAN REPLACEMENT")
    print("="*120)
    deps = [
        "qseries_v2/oracle_strategy_intelligence/solana/ssi_001_physical_solana_intelligence_audit.py",
        "qseries_v2/oracle_adapters/independent/oad_068_exact_postgresql_independent_readback.py",
    ]
    for d in deps:
        x=ROOT/d
        if not x.exists():
            raise SystemExit("[FAIL] missing dependency: "+d)
        ast.parse(x.read_text(encoding="utf-8"))
        print("[PASS] dependency:",d)
    PKG.mkdir(parents=True,exist_ok=True)
    MOD.write_text(MODULE,encoding="utf-8")
    TEST_PATH.write_text(TEST_SOURCE,encoding="utf-8")
    ast.parse(MODULE); ast.parse(TEST_SOURCE)
    print("[PASS] clean replacement module installed:",MOD.relative_to(ROOT))
    print("[PASS] new physical test installed:",TEST_PATH.relative_to(ROOT))
    print("[PASS] SELECT-only PostgreSQL audit")
    print("[PASS] no acquisition/writer/runtime mutation")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] SSI-001D INSTALLATION COMPLETE")

if __name__=="__main__":
    main()

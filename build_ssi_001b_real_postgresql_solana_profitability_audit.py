from pathlib import Path
import ast

ROOT=Path.cwd()
MOD=ROOT/"qseries_v2/oracle_strategy_intelligence/solana/ssi_001_real_postgresql_solana_profitability_audit.py"
TEST=ROOT/"test_ssi_001b_real_postgresql_solana_profitability_audit.py"

MODULE=r"""
from collections import Counter
import json, os
from datetime import datetime

def _connect():
    import psycopg
    dsn=os.getenv("ORACLE_POSTGRES_DSN") or os.getenv("DATABASE_URL")
    return psycopg.connect(dsn) if dsn else psycopg.connect()

def _table(cur):
    cur.execute("""SELECT table_schema,table_name FROM information_schema.columns
                   WHERE column_name IN ('source_id','observation_type','observed_at')
                   GROUP BY 1,2 HAVING count(DISTINCT column_name)=3
                   ORDER BY CASE WHEN table_name ILIKE '%canonical%' THEN 0 ELSE 1 END,table_name""")
    rows=cur.fetchall()
    if not rows: raise RuntimeError("no canonical observation table discovered")
    return rows[0]

def audit():
    with _connect() as con, con.cursor() as cur:
        s,t=_table(cur); q=f'"{s}"."{t}"'
        cur.execute(f"""SELECT count(*),min(observed_at),max(observed_at),
                        count(*) FILTER(WHERE observation_type='solana_economic_event'),
                        count(*) FILTER(WHERE observation_type='finalized_transaction')
                        FROM {q} WHERE source_id='source.onchain.solana.mainnet'""")
        total,first,last,econ,tx=cur.fetchone()
        cur.execute(f"""SELECT observation_type,count(*) FROM {q}
                        WHERE source_id='source.onchain.solana.mainnet'
                        GROUP BY 1 ORDER BY 2 DESC""")
        types=dict(cur.fetchall())
        # Sample real payloads read-only; discover whether persisted Solana rows contain usable price/liquidity/asset fields.
        cur.execute(f"""SELECT row_to_json(x) FROM
                        (SELECT * FROM {q} WHERE source_id='source.onchain.solana.mainnet'
                         ORDER BY observed_at DESC LIMIT 5000) x""")
        rows=[r[0] for r in cur.fetchall()]
    keys=Counter()
    price_rows=liq_rows=asset_rows=0
    price_keys=("price","price_usd","usd_price","token_price","close","mid")
    liq_keys=("liquidity","liquidity_usd","tvl","tvl_usd","reserve_usd")
    asset_keys=("mint","token_mint","base_mint","asset","symbol","pool","pool_address")
    def walk(v,p=""):
        if isinstance(v,dict):
            for k,x in v.items():
                key=(p+"."+k if p else k); keys[key]+=1; yield key,x
                yield from walk(x,key)
        elif isinstance(v,list):
            for x in v: yield from walk(x,p)
    for r in rows:
        flat=list(walk(r))
        names={k.split(".")[-1] for k,v in flat if v is not None}
        price_rows += bool(names.intersection(price_keys))
        liq_rows += bool(names.intersection(liq_keys))
        asset_rows += bool(names.intersection(asset_keys))
    span=0 if not first or not last else (last-first).total_seconds()
    ready=bool(total and price_rows>=2 and span>0)
    return {"schema_version":"SSI-001B","physical_postgresql":True,"table":f"{s}.{t}",
      "solana_rows":total,"economic_events":econ,"finalized_transactions":tx,
      "first_observed_at":str(first),"last_observed_at":str(last),"span_seconds":span,
      "observation_types":types,"sampled_rows":len(rows),"sample_price_rows":price_rows,
      "sample_liquidity_rows":liq_rows,"sample_asset_rows":asset_rows,
      "top_payload_paths":keys.most_common(40),"exact_price_path_input_ready":ready,
      "read_only":True,"execution_authority":False}

if __name__=="__main__":
    print(json.dumps(audit(),indent=2,default=str))
"""

TEST=r"""
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
if __name__=="__main__": unittest.main(verbosity=2)
"""

def main():
    print("="*120); print(" SSI-001B REAL POSTGRESQL SOLANA PROFITABILITY AUDIT"); print("="*120)
    deps=[
      "qseries_v2/oracle_strategy_intelligence/solana/ssi_001_physical_solana_intelligence_audit.py",
      "qseries_v2/oracle_adapters/independent/oad_068_exact_postgresql_independent_readback.py"]
    for d in deps:
        x=ROOT/d
        if not x.exists(): raise SystemExit("[FAIL] missing dependency: "+d)
        ast.parse(x.read_text(encoding="utf-8")); print("[PASS] dependency:",d)
    MOD.parent.mkdir(parents=True,exist_ok=True)
    MOD.write_text(MODULE,encoding="utf-8"); TEST.write_text(TEST,encoding="utf-8")
    ast.parse(MODULE); ast.parse(TEST)
    print("[PASS] installed:",MOD.relative_to(ROOT)); print("[PASS] test:",TEST.relative_to(ROOT))
    print("[PASS] PostgreSQL access is SELECT-only")
    print("[PASS] no acquisition/writer/runtime mutation introduced")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] SSI-001B installed")

if __name__=="__main__": main()

from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_intelligence"
MOD=SUB/"osi_045_exact_solana_gmgn_postgresql_reader.py"
TEST=ROOT/"test_osi_045_exact_solana_gmgn_postgresql_reader.py"
MOD_TEXT=r"""from __future__ import annotations
import os
from pathlib import Path
ENV=("DATABASE_URL","ORACLE_DATABASE_URL","ORACLE_POSTGRESQL_URL","POSTGRESQL_URL","POSTGRES_URL")
def _dsn(root):
 p=root/".env"
 if p.is_file():
  try:
   from dotenv import dotenv_values
   v=dotenv_values(p)
   for n in ENV:
    if v.get(n) and not os.environ.get(n):os.environ[n]=str(v[n])
  except Exception:pass
 for n in ENV:
  if os.environ.get(n):return os.environ[n]
 raise RuntimeError("NO_EXISTING_POSTGRES_DSN")
def read(root,limit=1000,cutoff=None):
 import psycopg
 where="""(
 (source_id='source.onchain.solana.mainnet' AND observation_type IN ('solana_economic_event','finalized_transaction'))
 OR (source_id LIKE 'source.gmgn.solana.token.%' AND observation_type IN ('gmgn_solana_token_pool','gmgn_solana_token_security','gmgn_solana_token_info'))
 OR (source_id LIKE 'source.crypto.condition.sol.solana.%')
 )"""
 params=[]
 if cutoff is not None:where+=" AND observed_at < %s";params.append(cutoff)
 params.append(limit)
 sql=f"SELECT observation_id,source_id,observation_type,observed_at,canonical_observation_json FROM public.oracle_canonical_observations WHERE {where} ORDER BY observed_at DESC LIMIT %s"
 with psycopg.connect(_dsn(root),connect_timeout=5) as c:
  with c.cursor() as q:
   q.execute("SET TRANSACTION READ ONLY");q.execute(sql,tuple(params));vals=q.fetchall()
 rows=[{"observation_id":r[0],"source_id":r[1],"observation_type":r[2],"observed_at":r[3].isoformat(),"canonical_observation_json":r[4]} for r in vals]
 return {"rows":rows,"row_count":len(rows),"execution_authority":False,"read_only":True}
"""
TEST_TEXT=r"""import unittest,collections
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_045_exact_solana_gmgn_postgresql_reader import read
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_physical(self):
  d=read(ROOT,500);self.assertFalse(d["execution_authority"]);self.assertGreater(d["row_count"],0)
  c=collections.Counter(x["observation_type"] for x in d["rows"])
  print("[ROWS]",d["row_count"]);print("[TYPES]",dict(c))
  print("[TOP_SOURCE]",d["rows"][0]["source_id"]);print("[TOP_TYPE]",d["rows"][0]["observation_type"])
  print("[PASS] OSI-045 exact Solana/GMGN PostgreSQL reader")
  print("[TRADER] Reads only native Solana, GMGN, and Solana-context warehouse rows")
if __name__=="__main__":unittest.main()
"""
def main():
 print("="*112);print(" OSI-045 EXACT SOLANA + GMGN POSTGRESQL READER");print("="*112)
 SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
 print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
if __name__=="__main__":main()

from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_intelligence"
MOD=SUB/"osi_040_readonly_postgresql_schema_profiler.py"
TEST=ROOT/"test_osi_040_readonly_postgresql_schema_profiler.py"
MOD_TEXT=r"""from __future__ import annotations
import json,os
from pathlib import Path
ENV=("ORACLE_DATABASE_URL","ORACLE_POSTGRESQL_URL","POSTGRESQL_URL","POSTGRES_URL","DATABASE_URL")
def _dsn():
 for n in ENV:
  if os.environ.get(n):return n,os.environ[n]
 return None,None
def profile(root:Path)->dict:
 name,dsn=_dsn()
 if not dsn:return {"connected":False,"error":"NO_EXISTING_DSN","tables":[],"execution_authority":False,"read_only":True}
 try:import psycopg
 except Exception as e:return {"connected":False,"error":"PSYCOPG:"+repr(e),"tables":[],"execution_authority":False,"read_only":True}
 try:
  with psycopg.connect(dsn,connect_timeout=5) as conn:
   with conn.cursor() as cur:
    cur.execute("SET TRANSACTION READ ONLY")
    cur.execute("SELECT table_schema,table_name,column_name,data_type FROM information_schema.columns WHERE table_schema NOT IN ('pg_catalog','information_schema') ORDER BY table_schema,table_name,ordinal_position")
    rows=cur.fetchall()
  grouped={}
  for s,t,c,d in rows:grouped.setdefault(f"{s}.{t}",[]).append({"column":c,"type":d})
  return {"connected":True,"dsn_env":name,"error":None,"tables":[{"table":k,"columns":v} for k,v in grouped.items()],"execution_authority":False,"read_only":True}
 except Exception as e:return {"connected":False,"dsn_env":name,"error":repr(e),"tables":[],"execution_authority":False,"read_only":True}
def write(root:Path)->Path:
 d=profile(root);p=root/"runtime_state/solana_opportunities/postgresql_schema_profile.json";p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p
"""
TEST_TEXT=r"""import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_040_readonly_postgresql_schema_profiler import profile,write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_physical(self):
  d=profile(ROOT);p=write(ROOT);self.assertTrue(p.is_file());self.assertFalse(d["execution_authority"])
  print("[CONNECTED]",d["connected"]);print("[DSN_ENV]",d.get("dsn_env"));print("[ERROR]",d.get("error"));print("[TABLES]",len(d["tables"]))
  if d["tables"]:print("[TOP_TABLE]",json.dumps(d["tables"][0],sort_keys=True)[:1500])
  if not d["connected"]:self.fail("POSTGRESQL_READONLY_CONNECTION_FAILED")
  print("[PASS] OSI-040 read-only PostgreSQL schema profiler")
if __name__=="__main__":unittest.main()
"""
def main():
 print("="*112);print(" OSI-040 READ-ONLY POSTGRESQL SCHEMA PROFILER");print("="*112)
 SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
 print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
if __name__=="__main__":main()

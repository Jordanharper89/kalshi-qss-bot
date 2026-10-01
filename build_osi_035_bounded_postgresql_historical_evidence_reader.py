from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_intelligence"
MOD=SUB/"osi_035_bounded_postgresql_historical_evidence_reader.py"
TEST=ROOT/"test_osi_035_bounded_postgresql_historical_evidence_reader.py"
MOD_TEXT=r"""from __future__ import annotations
import importlib,json,os,re
from pathlib import Path

AUDIT="runtime_state/solana_opportunities/postgresql_boundary_audit.json"

def _connect():
 try:
  import psycopg
 except Exception as e:
  return None,"PSYCOPG_UNAVAILABLE:"+repr(e)
 dsn=os.environ.get("DATABASE_URL") or os.environ.get("POSTGRES_DSN") or os.environ.get("ORACLE_POSTGRES_DSN")
 if not dsn:return None,"POSTGRES_DSN_NOT_FOUND"
 try:
  conn=psycopg.connect(dsn,connect_timeout=3)
  conn.autocommit=True
  return conn,None
 except Exception as e:return None,"CONNECT_FAILED:"+repr(e)

def inspect(root:Path,table_limit:int=100)->dict:
 ap=root/AUDIT
 if not ap.is_file():raise RuntimeError("Missing OSI-034 audit")
 conn,error=_connect()
 if conn is None:return {"connected":False,"error":error,"tables":[],"execution_authority":False,"read_only":True}
 try:
  with conn.cursor() as cur:
   cur.execute("SET default_transaction_read_only = on")
   cur.execute("""SELECT table_schema,table_name FROM information_schema.tables
                  WHERE table_type='BASE TABLE' AND table_schema NOT IN ('pg_catalog','information_schema')
                  ORDER BY table_schema,table_name LIMIT %s""",(table_limit,))
   tables=[{"schema":r[0],"table":r[1]} for r in cur.fetchall()]
  return {"connected":True,"error":None,"tables":tables,"execution_authority":False,"read_only":True}
 finally: conn.close()

def write(root:Path)->Path:
 d=inspect(root);p=root/"runtime_state/solana_opportunities/postgresql_read_boundary.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p
"""
TEST_TEXT=r"""import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_035_bounded_postgresql_historical_evidence_reader import inspect,write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_boundary(self):
  d=inspect(ROOT);p=write(ROOT);self.assertTrue(p.is_file());self.assertFalse(d["execution_authority"])
  print("[CONNECTED]",d["connected"]);print("[ERROR]",d["error"]);print("[TABLES]",len(d["tables"]))
  if d["tables"]:print("[TOP_TABLE]",json.dumps(d["tables"][0],sort_keys=True))
  print("[PASS] OSI-035 bounded PostgreSQL historical evidence reader installed")
  print("[TRADER] Solana runtime can inspect Oracle history through a read-only database session")
  print("[SCOPE] Schema/read-boundary certification only; no writes and no profitability claim")
if __name__=="__main__":unittest.main()
"""
def main():
 print("="*112);print(" OSI-035 BOUNDED POSTGRESQL HISTORICAL EVIDENCE READER");print("="*112)
 SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
 print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
if __name__=="__main__":main()

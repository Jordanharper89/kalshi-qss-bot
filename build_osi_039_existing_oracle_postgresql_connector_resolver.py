from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_intelligence"
MOD=SUB/"osi_039_existing_oracle_postgresql_connector_resolver.py"
TEST=ROOT/"test_osi_039_existing_oracle_postgresql_connector_resolver.py"
MOD_TEXT=r"""from __future__ import annotations
import json,os,re
from pathlib import Path
ENV_NAMES=("ORACLE_DATABASE_URL","ORACLE_POSTGRESQL_URL","POSTGRESQL_URL","POSTGRES_URL","DATABASE_URL")
def resolve(root:Path)->dict:
 found=[]
 for name in ENV_NAMES:
  if os.environ.get(name):found.append(name)
 modules=[]
 for p in (root/"qseries_v2").rglob("*.py"):
  try:t=p.read_text(encoding="utf-8",errors="replace")
  except Exception:continue
  if "psycopg" not in t.lower() and "postgres" not in t.lower():continue
  hits=[]
  for n,line in enumerate(t.splitlines(),1):
   low=line.lower()
   if "psycopg.connect" in low or "psycopg2.connect" in low or any(x.lower() in low for x in ENV_NAMES):
    hits.append({"line":n,"text":line[:700]})
  if hits:modules.append({"module":str(p.relative_to(root)),"matches":hits[:80]})
 return {"revision":"OSI_039","present_environment_names":found,"candidate_modules":modules[:150],
  "execution_authority":False,"read_only":True}
def write(root:Path)->Path:
 d=resolve(root);p=root/"runtime_state/solana_opportunities/postgresql_connector_resolver.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p
"""
TEST_TEXT=r"""import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_039_existing_oracle_postgresql_connector_resolver import resolve,write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_physical(self):
  d=resolve(ROOT);p=write(ROOT);self.assertTrue(p.is_file());self.assertFalse(d["execution_authority"])
  print("[ENV_PRESENT]",json.dumps(d["present_environment_names"]))
  print("[CONNECTOR_MODULES]",len(d["candidate_modules"]))
  if d["candidate_modules"]:print("[TOP_CONNECTOR]",json.dumps(d["candidate_modules"][0],sort_keys=True))
  if not d["present_environment_names"]:self.fail("NO_EXISTING_ORACLE_POSTGRES_ENVIRONMENT_VARIABLE_PRESENT")
  print("[PASS] OSI-039 existing Oracle PostgreSQL connector resolver")
  print("[TRADER] Reuses Oracle's real database connection instead of inventing a second credential path")
if __name__=="__main__":unittest.main()
"""
def main():
 print("="*112);print(" OSI-039 EXISTING ORACLE POSTGRESQL CONNECTOR RESOLVER");print("="*112)
 SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
 print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
if __name__=="__main__":main()

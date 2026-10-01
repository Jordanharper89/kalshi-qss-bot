from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_intelligence"
MOD=SUB/"osi_034_postgresql_evidence_boundary_audit.py"
TEST=ROOT/"test_osi_034_postgresql_evidence_boundary_audit.py"
MOD_TEXT=r"""from __future__ import annotations
import ast,json,re
from pathlib import Path

KEYS=("postgres","psycopg","sqlalchemy","information_schema","select ","insert into","create table","database_url","dsn")
def audit(root:Path)->dict:
 hits=[]
 for p in (root/"qseries_v2").rglob("*.py"):
  try:text=p.read_text(encoding="utf-8",errors="replace")
  except Exception:continue
  low=text.lower()
  if not any(k in low for k in KEYS):continue
  lines=[]
  for n,line in enumerate(text.splitlines(),1):
   if any(k in line.lower() for k in KEYS):lines.append({"line":n,"text":line[:700]})
  hits.append({"module":str(p.relative_to(root)),"matches":lines[:250]})
 return {"revision":"OSI_034","postgres_modules":hits,"module_count":len(hits),
  "execution_authority":False,"read_only":True,
  "purpose":"Find existing PostgreSQL read/write pavement for bounded Solana evidence reads."}
def write(root:Path)->Path:
 d=audit(root);p=root/"runtime_state/solana_opportunities/postgresql_boundary_audit.json"
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p
"""
TEST_TEXT=r"""import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_034_postgresql_evidence_boundary_audit import audit,write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_physical(self):
  d=audit(ROOT);p=write(ROOT);self.assertTrue(p.is_file());self.assertFalse(d["execution_authority"])
  print("[REPORT]",p);print("[POSTGRES_MODULES]",d["module_count"])
  if d["postgres_modules"]:print("[TOP_MODULE]",d["postgres_modules"][0]["module"])
  if not d["postgres_modules"]:self.fail("NO_EXISTING_POSTGRESQL_PAVEMENT_FOUND")
  print("[PASS] OSI-034 PostgreSQL evidence boundary audit")
  print("[TRADER] Finds Oracle's existing historical evidence warehouse boundary instead of creating another database")
  print("[SCOPE] Read-only source audit")
if __name__=="__main__":unittest.main()
"""
def main():
 print("="*112);print(" OSI-034 POSTGRESQL EVIDENCE BOUNDARY AUDIT");print("="*112)
 SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
 print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
if __name__=="__main__":main()

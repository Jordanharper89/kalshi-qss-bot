from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_intelligence"
MOD=SUB/"osi_041_solana_relevant_postgresql_table_classifier.py"
TEST=ROOT/"test_osi_041b_canonical_solana_postgresql_table_classifier.py"
MOD_TEXT=r"""from __future__ import annotations
import json
from pathlib import Path
TABLE_TERMS=("oracle","observation","canonical","history","event","source")
COLUMN_TERMS=("canonical_observation_json","observation_type","source_id","observed_at","jsonb","payload","data")
def classify(root:Path)->dict:
 p=root/"runtime_state/solana_opportunities/postgresql_schema_profile.json"
 d=json.loads(p.read_text(encoding="utf-8"))
 out=[]
 for t in d.get("tables",[]):
  table=t["table"];cols=t["columns"]
  names=[str(x["column"]).lower() for x in cols];types=[str(x["type"]).lower() for x in cols]
  text=(table+" "+" ".join(names)+" "+" ".join(types)).lower()
  score=sum(2 for k in TABLE_TERMS if k in table.lower())+sum(1 for k in COLUMN_TERMS if k in text)
  has_time="observed_at" in names
  has_json=any(x["column"]=="canonical_observation_json" and x["type"]=="jsonb" for x in cols)
  if score>0:out.append({"table":table,"score":score,"has_observed_at":has_time,"has_canonical_json":has_json,"columns":cols})
 out.sort(key=lambda x:(not x["has_canonical_json"],not x["has_observed_at"],-x["score"],x["table"]))
 return {"revision":"OSI_041B","candidates":out,"candidate_count":len(out),"execution_authority":False,"read_only":True}
def write(root:Path)->Path:
 d=classify(root);p=root/"runtime_state/solana_opportunities/solana_postgresql_tables.json";p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p
"""
TEST_TEXT=r"""import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_041_solana_relevant_postgresql_table_classifier import classify,write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_physical(self):
  d=classify(ROOT);p=write(ROOT);self.assertFalse(d["execution_authority"])
  print("[CANDIDATE_TABLES]",d["candidate_count"])
  if d["candidates"]:print("[TOP_CANDIDATE]",json.dumps(d["candidates"][0],sort_keys=True)[:1800])
  if not d["candidates"]:self.fail("NO_CANONICAL_POSTGRESQL_EVIDENCE_TABLES")
  self.assertTrue(any(x["has_canonical_json"] for x in d["candidates"]),msg="NO_CANONICAL_JSONB_TABLE")
  print("[PASS] OSI-041B canonical PostgreSQL evidence table classifier")
  print("[TRADER] Prioritizes Oracle's canonical JSONB warehouse instead of guessing flat Solana tables")
if __name__=="__main__":unittest.main()
"""
def main():
 print("="*112);print(" OSI-041B CANONICAL POSTGRESQL EVIDENCE TABLE CLASSIFIER");print("="*112)
 SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
 print("[PASS] replaced:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
if __name__=="__main__":main()

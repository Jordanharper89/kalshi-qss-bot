from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_scanner_runtime"
MOD=SUB/"usls_149_phase7_program_local_liquidity_candidate_gate.py"
TEST=ROOT/"test_usls_149_phase7_program_local_liquidity_candidate_gate.py"

MOD_TEXT=r"""from __future__ import annotations
import json
from pathlib import Path
SRC="runtime_state/solana_opportunities/solana_scanner/phase7_live_program_account_roles.json"

def run(root):
 d=json.loads((Path(root)/SRC).read_text(encoding="utf-8"));rows=[];fam={}
 for x in d.get("rows",[]):
  candidates=[]
  for ix in x.get("matched_instructions",[]):
   changes=ix.get("changed_token_accounts") or []
   # Require >=2 distinct changing token accounts in the same exact protocol instruction.
   uniq={c.get("account"):c for c in changes if c.get("account")}
   if len(uniq)<2:continue
   signs={1 if c.get("delta_raw",0)>0 else -1 if c.get("delta_raw",0)<0 else 0 for c in uniq.values()}
   if not ({1,-1}<=signs):continue
   candidates.append({"level":ix.get("level"),"instruction_index":ix.get("instruction_index"),
    "parent_index":ix.get("parent_index"),"accounts":list(uniq.values()),
    "candidate_state":"PROGRAM_LOCAL_OPPOSING_TOKEN_FLOW_PAIR"})
  rows.append({"family":x["family"],"trade_signature":x["trade_signature"],
   "liquidity_candidates":candidates,"candidate_count":len(candidates),
   "pool_vault_certified":False,"execution_authority":False})
  z=fam.setdefault(x["family"],{"rows":0,"with_candidate":0})
  z["rows"]+=1;z["with_candidate"]+=bool(candidates)
 return {"revision":"USLS_149","row_count":len(rows),"family_support":fam,"rows":rows,
  "candidate_semantics":"TWO_OR_MORE_OPPOSING_CHANGED_TOKEN_ACCOUNTS_INSIDE_SAME_TARGET_PROGRAM_INSTRUCTION",
  "pool_vault_certification":"NOT_CLAIMED",
  "next_boundary":"PROGRAM_LOCAL_RESERVE_REFERENCE_MATERIALIZATION",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=run(root)
 p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase7_program_local_liquidity_candidates.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8")
 return p,d
"""

TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_149_phase7_program_local_liquidity_candidate_gate import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT)
  n=sum(v["with_candidate"] for v in d["family_support"].values())
  print("[STATE]",json.dumps({"row_count":d["row_count"],"candidate_rows":n,
   "family_support":d["family_support"]},sort_keys=True))
  self.assertGreater(d["row_count"],0)
  self.assertGreater(n,0,"NO_PROGRAM_LOCAL_OPPOSING_FLOW_CANDIDATES")
  self.assertEqual(d["pool_vault_certification"],"NOT_CLAIMED")
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-149 program-local liquidity candidate gate")
  print("[PASS] opposing token-flow pairs retained as candidates, not mislabeled as certified vaults")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""
SUB.mkdir(parents=True,exist_ok=True)
MOD.write_text(MOD_TEXT,encoding="utf-8"); TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")

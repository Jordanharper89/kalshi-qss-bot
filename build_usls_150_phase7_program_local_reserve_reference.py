from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_scanner_runtime"
MOD=SUB/"usls_150_phase7_program_local_reserve_reference.py"
TEST=ROOT/"test_usls_150_phase7_program_local_reserve_reference.py"

MOD_TEXT=r"""from __future__ import annotations
import json
from pathlib import Path
SRC="runtime_state/solana_opportunities/solana_scanner/phase7_program_local_liquidity_candidates.json"

def run(root):
 d=json.loads((Path(root)/SRC).read_text(encoding="utf-8"));rows=[];fam={}
 for x in d.get("rows",[]):
  refs=[]
  for c in x.get("liquidity_candidates",[]):
   accts=[]
   for a in c.get("accounts",[]):
    dec=a.get("decimals")
    pre=a.get("pre_amount_raw");post=a.get("post_amount_raw")
    pre_ui=(pre/(10**dec)) if isinstance(pre,(int,float)) and isinstance(dec,int) else None
    post_ui=(post/(10**dec)) if isinstance(post,(int,float)) and isinstance(dec,int) else None
    accts.append({**a,"pre_amount_ui":pre_ui,"post_amount_ui":post_ui})
   refs.append({"instruction_index":c.get("instruction_index"),
    "parent_index":c.get("parent_index"),"accounts":accts,
    "reference_state":"PROGRAM_LOCAL_PRE_POST_TOKEN_BALANCE_REFERENCE"})
  rows.append({"family":x["family"],"trade_signature":x["trade_signature"],
   "reserve_references":refs,"reference_count":len(refs),
   "reference_is_certified_pool_liquidity":False,"execution_authority":False})
  z=fam.setdefault(x["family"],{"rows":0,"with_reference":0})
  z["rows"]+=1;z["with_reference"]+=bool(refs)
 return {"revision":"USLS_150","row_count":len(rows),"family_support":fam,"rows":rows,
  "reference_semantics":"PROGRAM_LOCAL_TOKEN_BALANCE_REFERENCE_NOT_YET_CERTIFIED_POOL_LIQUIDITY",
  "next_boundary":"EXTENDED_LIVE_COHORT_FOR_UNOBSERVED_FAMILIES",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=run(root)
 p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase7_program_local_reserve_reference.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8")
 return p,d
"""

TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_150_phase7_program_local_reserve_reference import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT)
  n=sum(v["with_reference"] for v in d["family_support"].values())
  print("[STATE]",json.dumps({"row_count":d["row_count"],"reference_rows":n,
   "family_support":d["family_support"],"next_boundary":d["next_boundary"]},sort_keys=True))
  self.assertGreater(n,0,"NO_PROGRAM_LOCAL_PRE_POST_REFERENCES")
  self.assertIn("NOT_YET_CERTIFIED_POOL_LIQUIDITY",d["reference_semantics"])
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-150 program-local reserve reference")
  print("[PASS] pre/post balance references materialized without overclaiming certified pool liquidity")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""
SUB.mkdir(parents=True,exist_ok=True)
MOD.write_text(MOD_TEXT,encoding="utf-8"); TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")

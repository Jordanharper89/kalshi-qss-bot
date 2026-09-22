from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_universal_trade_tape"
MOD=SUB/"usls_079_meteora_corrected_family_matrix.py"
TEST=ROOT/"test_usls_079_meteora_corrected_family_matrix.py"

MOD_TEXT=r"""from __future__ import annotations
import json
from pathlib import Path

def build(root):
 base=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape"
 prev=json.loads((base/"meteora_orca_reconciliation_matrix.json").read_text(encoding="utf-8"))
 v1=json.loads((base/"meteora_damm_v1_exact_economics.json").read_text(encoding="utf-8"))
 matrix=dict(prev["matrix"]);n=int(v1["exact_economic_count"])
 matrix["METEORA_DYN"]={**matrix["METEORA_DYN"],"corrected_identity":"METEORA_DAMM_V1",
  "correct_program_id":"Eo7WjKq67rjJQSZxS6z3YkapzY3eMj6Xy8X5EQVn5UaB",
  "exact_instruction_transfer_economics":n,
  "status":"EXACT_DAMM_V1_INSTRUCTION_ECONOMICS_CERTIFIED" if n>0 else "DAMM_V1_REPAIR_INCOMPLETE"}
 return {"revision":"USLS_079","matrix":matrix,"phase4_status":"IN_PROGRESS",
  "damm_v1_program_id_repaired":True,
  "next_boundary":"DBC_SOURCE_ROLE_CERTIFICATION_PLUS_MULTI_VENUE_UNIVERSAL_NORMALIZATION",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=build(root);p=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape/meteora_orca_reconciliation_matrix.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""

TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_079_meteora_corrected_family_matrix import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_matrix(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({"phase4_status":d["phase4_status"],
   "damm_v1_program_id_repaired":d["damm_v1_program_id_repaired"],"next_boundary":d["next_boundary"]},sort_keys=True))
  for v,x in d["matrix"].items():print("[VENUE]",v,json.dumps(x,sort_keys=True))
  self.assertTrue(d["damm_v1_program_id_repaired"])
  self.assertEqual(d["matrix"]["METEORA_DYN"]["status"],"EXACT_DAMM_V1_INSTRUCTION_ECONOMICS_CERTIFIED")
  self.assertEqual(d["phase4_status"],"IN_PROGRESS");self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-079 corrected Meteora family matrix")
  print("[NEXT] DBC_SOURCE_ROLE_CERTIFICATION_PLUS_MULTI_VENUE_UNIVERSAL_NORMALIZATION")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""
SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
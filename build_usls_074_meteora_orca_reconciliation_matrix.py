from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_universal_trade_tape"
MOD=SUB/"usls_074_meteora_orca_reconciliation_matrix.py"
TEST=ROOT/"test_usls_074_meteora_orca_reconciliation_matrix.py"

MOD_TEXT=r"""from __future__ import annotations
import json
from pathlib import Path
VENUES=("METEORA_DBC","METEORA_DAMM","METEORA_DLMM","METEORA_DYN","ORCA")

def build(root):
 base=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape"
 m=json.loads((base/"meteora_orca_physical_decoder_matrix.json").read_text(encoding="utf-8"))
 r=json.loads((base/"meteora_orca_exact_transfer_reconciliation.json").read_text(encoding="utf-8"))
 d=json.loads((base/"meteora_dbc_physical_role_discovery.json").read_text(encoding="utf-8"))
 out={}
 for v in VENUES:
  prev=m["matrix"][v];exact=int(r["venue_exact_counts"].get(v,0))
  if v=="METEORA_DBC":
   status="PHYSICAL_ROLE_DISCOVERY_PENDING_SOURCE_CERTIFICATION"
  elif v=="METEORA_DYN":
   status=prev["status"]
  elif exact>0:
   status="EXACT_INSTRUCTION_TRANSFER_ECONOMICS_POOL_ROLE_CERTIFIED_OR_PARTIAL"
  elif prev["exact_swap_instructions"]>0:
   status="EXACT_SWAP_INSTRUCTION_TRANSFER_RECONCILIATION_PENDING"
  else:status=prev["status"]
  out[v]={**prev,"exact_instruction_transfer_economics":exact,"status":status}
 return {"revision":"USLS_074","matrix":out,"dbc_role_certified":d["role_certified"],
  "phase4_status":"IN_PROGRESS","next_boundary":"DBC_SOURCE_ROLE_CERTIFICATION_PLUS_DAMM_DLMM_ORCA_EXACT_NORMALIZATION",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=build(root);p=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape/meteora_orca_reconciliation_matrix.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""

TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_074_meteora_orca_reconciliation_matrix import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_matrix(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({"phase4_status":d["phase4_status"],"next_boundary":d["next_boundary"],"dbc_role_certified":d["dbc_role_certified"]},sort_keys=True))
  for v,x in d["matrix"].items():print("[VENUE]",v,json.dumps(x,sort_keys=True))
  self.assertEqual(d["phase4_status"],"IN_PROGRESS");self.assertFalse(d["dbc_role_certified"])
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-074 Meteora/Orca reconciliation matrix")
  print("[NEXT] DBC_SOURCE_ROLE_CERTIFICATION_PLUS_DAMM_DLMM_ORCA_EXACT_NORMALIZATION")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""
SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
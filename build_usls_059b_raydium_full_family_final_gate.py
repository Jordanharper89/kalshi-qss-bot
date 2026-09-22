from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_universal_trade_tape"
MOD=SUB/"usls_059b_raydium_full_family_final_gate.py"
TEST=ROOT/"test_usls_059b_raydium_full_family_final_gate.py"

MOD_TEXT=r"""from __future__ import annotations
import json
from pathlib import Path
FAMILIES=("RAYDIUM_V4","RAYDIUM_CPMM","RAYDIUM_CLMM","RAYDIUM_LAUNCHLAB")

def build(root):
 base=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape"
 hyd=json.loads((base/"raydium_family_completion_transactions.json").read_text(encoding="utf-8"))
 ix=json.loads((base/"raydium_exact_instruction_pool_roles.json").read_text(encoding="utf-8"))
 econ=json.loads((base/"raydium_exact_pair_orientation.json").read_text(encoding="utf-8"))
 ll=json.loads((base/"raydium_launchlab_completion_gate.json").read_text(encoding="utf-8"))
 matrix={}
 for v in FAMILIES:
  hydrated=int(hyd["hydrated_counts"].get(v,0));swaps=int(ix["venue_counts"].get(v,0))
  pools=int(ix["exact_pool_role_counts"].get(v,0))
  two=int(econ["venue_two_asset_counts"].get(v,0));quoted=int(econ["venue_exact_quote_counts"].get(v,0))
  if v=="RAYDIUM_LAUNCHLAB":
   status=ll["status"]
  elif quoted>0:status="EXACT_QUOTE_ORIENTED_TRADE_DECODER_CERTIFIED"
  elif two>0 and pools>0:status="EXACT_TWO_ASSET_TRADE_DECODER_CERTIFIED_QUOTE_ORIENTATION_CONDITIONAL"
  elif swaps>0:status="EXACT_SWAP_INSTRUCTION_CERTIFIED_ECONOMICS_PENDING"
  elif hydrated>0:status="HYDRATED_ACTIVITY_NO_EXACT_SWAP_IN_SAMPLE"
  else:status="BLOCKED_BY_NO_HYDRATABLE_LIVE_ACTIVITY"
  matrix[v]={"hydrated_transactions":hydrated,"exact_swap_instructions":swaps,
   "exact_pool_roles":pools,"exact_two_asset_swaps":two,"exact_quote_oriented_swaps":quoted,"status":status}
 closed=all(("CERTIFIED" in x["status"] or "BLOCKED_BY_" in x["status"] or "OBSERVED_NO_VERIFIED" in x["status"])
            for x in matrix.values())
 return {"revision":"USLS_059B","matrix":matrix,"raydium_family_boundary_closed":closed,
  "phase4_status":"IN_PROGRESS","next_boundary":"METEORA_ORCA_SHARED_DECODER_PLUGINS" if closed else "CONTINUE_RAYDIUM_REPAIR",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=build(root);p=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape/raydium_full_family_final_gate.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""
TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_059b_raydium_full_family_final_gate import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_final(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({"raydium_family_boundary_closed":d["raydium_family_boundary_closed"],
   "phase4_status":d["phase4_status"],"next_boundary":d["next_boundary"]},sort_keys=True))
  for v,x in d["matrix"].items():print("[RAYDIUM]",v,json.dumps(x,sort_keys=True))
  self.assertEqual(len(d["matrix"]),4)
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  if d["raydium_family_boundary_closed"]:
   print("[PASS] USLS-059B Raydium family boundary closed")
   print("[NEXT] METEORA_ORCA_SHARED_DECODER_PLUGINS")
  else:
   print("[BLOCKED] Raydium family still has unresolved non-evidence-backed gaps")
   print("[NEXT] CONTINUE_RAYDIUM_REPAIR")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""
SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")

import json,unittest
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

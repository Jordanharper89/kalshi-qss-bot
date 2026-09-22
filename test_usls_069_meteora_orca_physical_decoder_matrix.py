import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_069_meteora_orca_physical_decoder_matrix import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_matrix(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({"phase4_status":d["phase4_status"],"next_boundary":d["next_boundary"]},sort_keys=True))
  for v,x in d["matrix"].items():print("[VENUE]",v,json.dumps(x,sort_keys=True))
  self.assertEqual(len(d["matrix"]),5);self.assertEqual(d["phase4_status"],"IN_PROGRESS")
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-069 Meteora/Orca physical decoder matrix")
  print("[NEXT] METEORA_ORCA_EXACT_POOL_ROLE_AND_INSTRUCTION_ECONOMIC_RECONCILIATION")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()

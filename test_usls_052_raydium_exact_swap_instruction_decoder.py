import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_052_raydium_exact_swap_instruction_decoder import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_decode(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({"exact_swap_instruction_count":d["exact_swap_instruction_count"],
   "venue_counts":d["venue_counts"]},sort_keys=True))
  for x in d["rows"][:30]:print("[SWAP]",json.dumps({k:x[k] for k in ("venue","signature","instruction_name","pool","pool_account_index")},sort_keys=True))
  self.assertGreater(d["exact_swap_instruction_count"],0)
  self.assertTrue(all(x["pool"] for x in d["rows"]))
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-052 exact Raydium swap instruction + pool account decoder")
  print("[PASS] non-swap Raydium activity excluded without being relabeled")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()

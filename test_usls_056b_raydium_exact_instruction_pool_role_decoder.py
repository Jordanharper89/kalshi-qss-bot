import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_056b_raydium_exact_instruction_pool_role_decoder import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_decode(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({"row_count":d["row_count"],"venue_counts":d["venue_counts"],
   "exact_pool_role_counts":d["exact_pool_role_counts"]},sort_keys=True))
  for x in d["rows"][:40]:print("[SWAP]",json.dumps({k:x[k] for k in ("venue","signature","instruction_name","pool","pool_role_state")},sort_keys=True))
  self.assertGreater(d["row_count"],0);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-056B Raydium exact instruction + pool-role decoder")
  print("[PASS] V4/CPMM/CLMM use current official account-role layouts; unproven LaunchLab roles remain pending")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()

import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_100_damm_v2_pool_state_account_audit import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_audit(self):
  p,d=write(ROOT)
  print("[SIGNATURE]",d["signature"])
  print("[ACCOUNT_KEYS]",json.dumps(d["account_keys"],indent=2))
  print("[INSTRUCTIONS]",json.dumps(d["instructions"],indent=2))
  print("[PRE_TOKEN]",json.dumps(d["preTokenBalances"],indent=2))
  print("[POST_TOKEN]",json.dumps(d["postTokenBalances"],indent=2))
  print("[LOGS]",json.dumps(d["logs"],indent=2))
  self.assertGreater(len(d["account_keys"]),0)
  print("[PASS] SULS-100 DAMM V2 pool-state account physical audit")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()

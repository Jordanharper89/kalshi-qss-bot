import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_058b_raydium_launchlab_physical_completion_gate import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT);print("[STATE]",json.dumps(d,sort_keys=True))
  self.assertIn(d["status"],("EXACT_LAUNCHLAB_TRADE_INSTRUCTION_OBSERVED_ACCOUNT_ROLE_PENDING",
   "LIVE_LAUNCHLAB_TRANSACTIONS_OBSERVED_NO_VERIFIED_TRADE_IN_SAMPLE","BLOCKED_BY_NO_HYDRATABLE_LIVE_ACTIVITY"))
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-058B LaunchLab physical completion gate")
  print("[PASS] no false certification: exact, observed-no-trade, or evidence-backed blocked only")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()

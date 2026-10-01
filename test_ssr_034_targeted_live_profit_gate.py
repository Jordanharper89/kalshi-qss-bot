import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_profitability_runtime.ssr_034_targeted_live_profit_gate import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT);print("[STATE]",json.dumps(d,sort_keys=True));self.assertIn(d["state"],("TARGETED_RULE_OBSERVE","TARGETED_RULE_LIVE_READY_CANDIDATE"));self.assertFalse(d["profitability_claimed"])
  print("[PASS] SSR-034 targeted live profit gate")
if __name__=="__main__":unittest.main()

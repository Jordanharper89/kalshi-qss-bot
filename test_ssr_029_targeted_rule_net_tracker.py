import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_profitability_runtime.ssr_029_targeted_rule_net_tracker import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_net(self):
  p,d=write(ROOT);print("[STATE]",json.dumps(d,sort_keys=True))
  self.assertGreaterEqual(d["physical_friction_row_count"],1);self.assertFalse(d["profitability_claimed"]);print("[PASS] SSR-029 targeted rule net tracker")
if __name__=="__main__":unittest.main()

import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_profitability_runtime.ssr_031_targeted_rule_live_activation import ensure
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_activation(self):
  d=ensure(ROOT);print("[STATE]",json.dumps(d,sort_keys=True));self.assertIn("activation_unix",d);self.assertFalse(d["execution_authority"])
  print("[PASS] SSR-031 targeted rule live activation frozen")
if __name__=="__main__":unittest.main()

import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_profitability_runtime.ssr_022_time_ordered_rule_discovery import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_rules(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({"hypothesis_count":d["hypothesis_count"]},sort_keys=True));self.assertIn("TRAIN_ONLY",d["selection_semantics"]);self.assertFalse(d["execution_authority"]);print("[PASS] SSR-022 time-ordered rule discovery")
if __name__=="__main__":unittest.main()

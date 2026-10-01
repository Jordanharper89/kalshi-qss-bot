import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_profitability_runtime.ssr_027_targeted_rule_freeze_filter import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_filter(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({"matched_freeze_count":d["matched_freeze_count"]},sort_keys=True))
  self.assertFalse(d["execution_authority"]);print("[PASS] SSR-027 targeted rule freeze filter")
if __name__=="__main__":unittest.main()

import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_profitability_runtime.ssr_008_play_friction_attachment import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_friction(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({"play_count":d["play_count"],"friction_supported_play_count":d["friction_supported_play_count"]},sort_keys=True))
  self.assertFalse(d["cross_family_imputation"]);self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] SSR-008 play friction attachment")
if __name__=="__main__":unittest.main()

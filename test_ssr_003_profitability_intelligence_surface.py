import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_profitability_runtime.ssr_003_profitability_intelligence import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_surface(self):
  p,d=write(ROOT);print("[STATE]",json.dumps(d,sort_keys=True))
  self.assertIn(d["play_state"],("OBSERVE","CANDIDATE_EDGE_NOT_CERTIFIED","ABSTAIN"))
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] SSR-003 profitability intelligence surface")
  print("[STATE] play_state="+d["play_state"])
if __name__=="__main__":unittest.main()

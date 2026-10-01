import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_profitability_runtime.ssr_009_play_gate import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({"play_count":d["play_count"],"ready_count":d["ready_count"],"observe_count":d["observe_count"],"abstain_count":d["abstain_count"]},sort_keys=True))
  for x in d["plays"]:self.assertIn(x["play_state"],("READY","OBSERVE","ABSTAIN"))
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] SSR-009 READY / OBSERVE / ABSTAIN play gate")
  if d["ready_count"]==0:print("[INFO] no READY play yet; OBSERVE plays are still surfaced")
if __name__=="__main__":unittest.main()

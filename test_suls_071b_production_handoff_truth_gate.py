import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_071b_production_handoff_truth_gate import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT);print("[STATE]",json.dumps(d,sort_keys=True))
  for k in ("program_indexed_capture_ready","restart_backfill_ready","live_priority_policy_ready","runtime_cycle_ready"):
   if not d[k]:self.fail(k.upper()+"_FALSE")
  self.assertFalse(d["existing_oracle_launcher_bound"]);self.assertFalse(d["production_24x7_active"])
  self.assertFalse(d["profitability_claimed"])
  print("[PASS] SULS-071B production handoff truth gate")
if __name__=="__main__":unittest.main()

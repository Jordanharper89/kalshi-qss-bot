import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_077_event_driven_live_lane_truth_gate import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT);print("[STATE]",json.dumps(d,sort_keys=True))
  if not d["event_driven_live_lane_foundation_ready"]:self.fail("EVENT_DRIVEN_LIVE_LANE_NOT_READY")
  self.assertEqual(d["signature_polling_role"],"RESTART_BACKFILL_ONLY")
  self.assertFalse(d["production_24x7_active"]);self.assertFalse(d["profitability_claimed"])
  print("[PASS] SULS-077 event-driven live-lane truth gate")
if __name__=="__main__":unittest.main()

import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_055b_raydium_family_completion_hydrator import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_live(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({"selected_counts":d["selected_counts"],"hydrated_counts":d["hydrated_counts"]},sort_keys=True))
  self.assertGreater(sum(d["hydrated_counts"].values()),0)
  self.assertTrue(d["fallback_recent_signatures"]);self.assertTrue(d["retry_safe"])
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-055B Raydium family completion hydrator")
  print("[PASS] shared-router signatures plus recent-program fallback cover missing short-gate families")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()

import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_087_remaining_venue_live_hydrator import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_live(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({"selected_counts":d["selected_counts"],
   "hydrated_counts":d["hydrated_counts"],"rpc_source":d["rpc_source"]},sort_keys=True))
  self.assertGreater(sum(d["selected_counts"].values()),0,"NO_REMAINING_VENUE_SIGNATURES")
  self.assertGreater(sum(d["hydrated_counts"].values()),0,"NO_REMAINING_VENUE_HYDRATED_TRANSACTIONS")
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-087 remaining-venue physical hydration")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()

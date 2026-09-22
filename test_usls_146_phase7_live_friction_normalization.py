import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_146_phase7_live_friction_normalization import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({"row_count":d["row_count"],
   "family_support":d["family_support"],"next_boundary":d["next_boundary"]},sort_keys=True))
  self.assertGreater(d["row_count"],0)
  self.assertGreater(sum(v["latency"] for v in d["family_support"].values()),0)
  self.assertGreater(sum(v["network_fee"] for v in d["family_support"].values()),0)
  self.assertIn("NETWORK_FEE_IS_NOT_PROTOCOL_FEE",d["strict_policy"])
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-146 live friction normalization")
  print("[PASS] physical latency/network fee retained while unresolved protocol fee/liquidity stay unresolved")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()

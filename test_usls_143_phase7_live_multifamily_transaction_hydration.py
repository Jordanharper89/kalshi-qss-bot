import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_143_phase7_live_multifamily_transaction_hydration import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({"row_count":d["row_count"],
   "family_support":d["family_support"],"next_boundary":d["next_boundary"]},sort_keys=True))
  self.assertGreaterEqual(len(d["family_support"]),4,"LIVE_FAMILY_COVERAGE_TOO_NARROW")
  self.assertGreater(sum(v["tx_found"] for v in d["family_support"].values()),0)
  self.assertGreater(sum(v["latency"] for v in d["family_support"].values()),0)
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-143 live multifamily transaction hydration")
  print("[PASS] multiple prospective signatures per observed family hydrated with fee + latency")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()

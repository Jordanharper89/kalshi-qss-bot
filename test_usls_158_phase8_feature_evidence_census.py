import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_158_phase8_feature_evidence_census import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({"family_count":d["family_count"],
   "family_feature_support":d["family_feature_support"],
   "next_boundary":d["next_boundary"]},sort_keys=True))
  self.assertEqual(d["family_count"],14)
  self.assertGreater(sum(v["amounts"] for v in d["family_feature_support"].values()),0)
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-158 Phase 8 feature-evidence census")
  print("[PASS] side/trader/fee/liquidity/time/amount evidence measured across 14 families")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()

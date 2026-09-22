import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_161g4u2_phase8_live_certified_economics_producer_bridge import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_live(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({"ready_families":d["ready_families"],
   "producer_candidate_counts":d["producer_candidate_counts"],
   "live_target_signature_count":d["live_target_signature_count"],
   "producer_invoke_attempts":d["producer_invoke_attempts"],
   "live_certified_economic_row_count":d["live_certified_economic_row_count"],
   "family_support":d["family_support"],"next_boundary":d["next_boundary"]},sort_keys=True))
  self.assertGreater(d["live_target_signature_count"],0,"NO_LIVE_SIGNATURES_FOR_CERTIFIED_ECONOMICS_FAMILIES")
  self.assertGreater(sum(d["producer_candidate_counts"].values()),0,"NO_ARTIFACT_PRODUCER_CALLABLES_FOUND")
  self.assertGreater(d["live_certified_economic_row_count"],0,
   "CERTIFIED_PRODUCER_PATH_COULD_NOT_MATERIALIZE_FRESH_LIVE_ECONOMICS")
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-161G4U2 live certified-economics producer bridge")
  print("[PASS] fresh live signatures reached the exact artifact-producing code path")
  print("[NEXT] UNIVERSAL_PROSPECTIVE_SETUP_FREEZE")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()

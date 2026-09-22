import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_161g4u3_phase8_strict_live_economics_provenance_gate import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_live(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({"live_target_signature_count":d["live_target_signature_count"],
   "strict_invoke_attempts":d["strict_invoke_attempts"],
   "non_replayable_candidates_rejected":d["non_replayable_candidates_rejected"],
   "strict_live_economic_row_count":d["strict_live_economic_row_count"],
   "family_support":d["family_support"],"next_boundary":d["next_boundary"]},sort_keys=True))
  self.assertGreater(d["live_target_signature_count"],0,"NO_LIVE_TARGET_SIGNATURES")
  self.assertGreater(d["strict_live_economic_row_count"],0,
   "NO_STRICT_SIGNATURE_PROVEN_LIVE_ECONOMIC_ROWS")
  self.assertTrue(all(x["strict_live_provenance"] for x in d["rows"]))
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-161G4U3 strict live economics provenance")
  print("[PASS] each accepted row explicitly contains the same fresh live signature + market + price")
  print("[NEXT] UNIVERSAL_PROSPECTIVE_SETUP_FREEZE_STRICT")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()

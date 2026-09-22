import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_161c_phase8_live_outcome_source_capability_diagnostic import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_diag(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({"raw_row_count":d["raw_row_count"],
   "ready_family_count":d["ready_family_count"],
   "families_with_live_price_outcome_source":d["families_with_live_price_outcome_source"],
   "family_support":d["family_support"],
   "next_boundary":d["next_boundary"]},sort_keys=True))
  self.assertGreater(d["raw_row_count"],0,"NO_LIVE_UNIVERSAL_TRADE_ACTIVITY")
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-161C live outcome-source capability diagnostic")
  print("[PASS] measured whether live rows can support prospective price outcomes before building learner")
  print("[NEXT]",d["next_boundary"])
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()

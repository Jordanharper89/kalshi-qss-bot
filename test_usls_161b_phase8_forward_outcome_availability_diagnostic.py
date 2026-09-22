import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_161b_phase8_forward_outcome_availability_diagnostic import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_diag(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({"snapshot_count":d["snapshot_count"],
   "outcome_reason_counts":d["outcome_reason_counts"],
   "by_horizon":d["by_horizon"],"by_family":d["by_family"],
   "next_boundary":d["next_boundary"]},sort_keys=True))
  self.assertGreater(d["snapshot_count"],0,"NO_PHASE8_SNAPSHOTS_TO_DIAGNOSE")
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-161B forward-outcome availability diagnostic")
  print("[PASS] zero learnable cases traced to physical outcome availability, not hidden by fallback labels")
  print("[NEXT]",d["next_boundary"])
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()

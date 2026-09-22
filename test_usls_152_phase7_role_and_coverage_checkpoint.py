import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_152_phase7_role_and_coverage_checkpoint import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps(d,sort_keys=True))
  self.assertGreater(len(d["program_account_match_families"]),0)
  self.assertGreater(len(d["program_local_liquidity_candidate_families"]),0)
  self.assertGreater(len(d["program_local_reserve_reference_families"]),0)
  self.assertEqual(d["phase7_status"],"IN_PROGRESS")
  self.assertFalse(d["phase7_physically_certified"])
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-152 Phase 7 role + coverage checkpoint")
  print("[NEXT]",d["remaining_required_capability"])
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()

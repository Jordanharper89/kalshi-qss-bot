import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_106y_rate_safe_exact_birth_retry_gate import write
ROOT=Path(__file__).resolve().parent

class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT,max_attempts=3,max_items=14)
  print("[STATE]",json.dumps({
   "prior_rpc_error_count":d["prior_rpc_error_count"],
   "retry_candidate_count":d["retry_candidate_count"],
   "recovered_dispatch_count":d["recovered_dispatch_count"],
   "still_unresolved_count":d["still_unresolved_count"],
   "exact_birth_count":d["exact_birth_count"]},sort_keys=True))
  for x in d["retries"]:
   print("[RETRY]",json.dumps({
    "family":x["family"],"signature":x["signature"],"resolved":x["resolved"],
    "attempts":x["attempts"]},sort_keys=True))
  self.assertGreater(d["retry_candidate_count"],0,"NO_106X_RPC_ERRORS_TO_RETRY")
  self.assertTrue(d["rate_safe_retry"])
  self.assertGreater(d["recovered_dispatch_count"],0,"NO_RATE_LIMITED_DISPATCH_RECOVERED")
  self.assertFalse(d["identity_materialization_certified"])
  self.assertFalse(d["lifecycle_join_certified"])
  self.assertFalse(d["profitability_claimed"])
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-106Y rate-safe exact-birth retry gate")
  if d["exact_birth_count"]:
   print("[READY] exact birth recovered from previously rate-limited cohort")
  else:
   print("[WAIT] rate-limited cohort recovered; no exact birth in recovered transactions")
  print("[PASS] execution_authority=FALSE")

if __name__=="__main__":unittest.main()

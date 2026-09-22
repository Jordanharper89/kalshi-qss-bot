import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_107c_phase5_exact_lifecycle_join_repair import write
ROOT=Path(__file__).resolve().parent

class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({k:d[k] for k in (
   "tape_row_count","birth_count","trade_count","birth_identity_complete_count",
   "trade_rows_with_explicit_token","trade_rows_with_explicit_market",
   "trade_rows_containing_any_fresh_birth_address",
   "exact_identity_lifecycle_join_count","finding","required_next_boundary")},sort_keys=True))
  self.assertGreater(d["birth_count"],0,"NO_EXACT_BIRTH_ROWS_FROM_107B")
  self.assertEqual(d["birth_identity_complete_count"],d["birth_count"],
   "BIRTH_IDENTITY_NOT_COMPLETE")
  self.assertGreater(d["trade_count"],0,"NO_UNIVERSAL_TRADE_ROWS")
  self.assertTrue(d["no_family_time_only_join"])
  self.assertFalse(d["profitability_claimed"])
  self.assertFalse(d["execution_authority"])
  if d["exact_identity_lifecycle_join_count"]>0:
   print("[PASS] USLS-107C exact lifecycle join repair")
   print("[READY] PHASE5_CERTIFICATION")
  else:
   print("[PASS] USLS-107C join-root-cause physically isolated")
   print("[BLOCK] universal raw trade lane lacks exact token+market identity for fresh Pump births")
   print("[NEXT] EXACT_PUMP_TRADE_NORMALIZATION_INTO_SCANNER_TAPE")
  print("[PASS] execution_authority=FALSE")

if __name__=="__main__":unittest.main()

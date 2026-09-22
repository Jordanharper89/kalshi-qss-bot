import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_106p_scanner_raw_program_admission_before_classification import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT,seconds=12)
  print("[STATE]",json.dumps(d,sort_keys=True))
  self.assertGreater(d["notification_count"],0,"NO_UNIVERSAL_PROGRAM_ACTIVITY")
  self.assertGreater(d["persisted_new_rows"]+d["deduplicated_existing_rows"],0,"NO_RAW_PROGRAM_ACTIVITY_RETAINED")
  self.assertTrue(d["raw_admission_before_classification"])
  self.assertTrue(d["raw_known_program_retention"])
  self.assertEqual(d["unknown_retention"],"RETAIN_RAW_UNRESOLVED")
  self.assertFalse(d["lifecycle_join_certified"])
  self.assertFalse(d["profitability_claimed"])
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-106P scanner raw-program admission before classification")
  print("[PASS] universal known-program activity retained before birth filtering")
  print("[INFO] birth_hints_after_raw_admission=",d["birth_hints_after_raw_admission"])
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()

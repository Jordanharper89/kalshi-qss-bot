import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_106t_scanner_successful_transaction_hydration_gate import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT,max_samples=12)
  print("[STATE]",json.dumps({"raw_record_count":d["raw_record_count"],
   "probed_count":d["probed_count"],"successful_transaction_count":d["successful_transaction_count"],
   "failed_transaction_count":d["failed_transaction_count"],"rate_limited_count":d["rate_limited_count"],
   "finding":d["finding"],"next_boundary":d["next_boundary"]},sort_keys=True))
  for x in d["probes"]:print("[PROBE]",json.dumps(x,sort_keys=True))
  self.assertGreater(d["raw_record_count"],0,"RAW_PROGRAM_ACTIVITY_EMPTY")
  self.assertGreater(d["probed_count"],0,"NO_SIGNATURES_PROBED")
  self.assertGreater(d["successful_transaction_count"],0,"NO_SUCCESSFUL_TRANSACTION_IN_BOUNDED_SAMPLE")
  self.assertEqual(d["failed_tx_policy"],"RETAIN_RAW_ACTIVITY_BUT_EXCLUDE_FROM_EXACT_BIRTH_CERTIFICATION")
  self.assertFalse(d["certification_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-106T successful transaction hydration gate")
  print("[PASS] failed transactions retained raw but excluded from exact birth certification")
  print("[NEXT] EXACT_BIRTH_DECODING_FROM_SUCCESSFUL_HYDRATED_RAW_ACTIVITY")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()

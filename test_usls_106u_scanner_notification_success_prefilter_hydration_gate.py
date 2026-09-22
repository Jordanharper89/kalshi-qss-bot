import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_106u_scanner_notification_success_prefilter_hydration_gate import write
ROOT=Path(__file__).resolve().parent

class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT,max_hydrations=5)
  print("[STATE]",json.dumps({
   "raw_record_count":d["raw_record_count"],
   "notification_success_count":d["notification_success_count"],
   "notification_failed_count":d["notification_failed_count"],
   "hydration_probe_count":d["hydration_probe_count"],
   "hydrated_ok":d["hydrated_ok"],
   "finding":d["finding"]},sort_keys=True))
  print("[FAMILY_OUTCOMES]",json.dumps(d["family_outcomes"],sort_keys=True))
  for x in d["probes"]:print("[PROBE]",json.dumps(x,sort_keys=True))
  self.assertGreater(d["raw_record_count"],0,"RAW_PROGRAM_ACTIVITY_EMPTY")
  self.assertGreater(d["notification_success_count"],0,"NO_SUCCESSFUL_LOGS_SUBSCRIBE_NOTIFICATION_PRESENT")
  self.assertGreater(d["hydration_probe_count"],0,"NO_SUCCESSFUL_SIGNATURES_SELECTED_FOR_HYDRATION")
  self.assertGreater(d["hydrated_ok"],0,"SUCCESSFUL_NOTIFICATION_DID_NOT_HYDRATE")
  self.assertEqual(d["failed_notification_policy"],
   "RETAIN_RAW_ACTIVITY_EXCLUDE_FROM_EXACT_BIRTH_CERTIFICATION")
  self.assertFalse(d["certification_claimed"])
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-106U notification-success prefilter hydration gate")
  print("[PASS] failed transactions retained raw; successful notifications selected before RPC hydration")
  print("[NEXT] EXACT_BIRTH_DECODING_FROM_SUCCESSFUL_HYDRATED_RAW_ACTIVITY")
  print("[PASS] execution_authority=FALSE")

if __name__=="__main__":unittest.main()

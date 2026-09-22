import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_106q_scanner_raw_activity_hydration_truth_gate import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT,max_samples=30)
  print("[STATE]",json.dumps({"raw_record_count":d["raw_record_count"],
   "sampled_signatures":d["sampled_signatures"],"hydrated_ok":d["hydrated_ok"],
   "hydration_errors":d["hydration_errors"],"family_counts":d["family_counts"],
   "finding":d["finding"],"next_boundary":d["next_boundary"]},sort_keys=True))
  for x in d["samples"]:print("[SAMPLE]",json.dumps(x,sort_keys=True))
  self.assertGreater(d["raw_record_count"],0,"RAW_PROGRAM_ACTIVITY_EMPTY")
  self.assertGreater(d["sampled_signatures"],0,"NO_SIGNATURES_AVAILABLE_FOR_HYDRATION")
  self.assertGreater(d["hydrated_ok"],0,"NO_RAW_ACTIVITY_SIGNATURE_HYDRATED")
  self.assertFalse(d["certification_claimed"])
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-106Q raw-activity hydration truth gate")
  print("[PASS] scanner can hydrate retained raw activity before birth classification")
  print("[NEXT] EXACT_BIRTH_DECODING_FROM_HYDRATED_RAW_ACTIVITY")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()

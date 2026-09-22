import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_106o_scanner_birth_admission_filter_truth_audit import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_audit(self):
  p,d=write(ROOT,seconds=12)
  s=d["static"];l=d["live"]
  print("[STATE]",json.dumps({"finding":d["finding"],"required_repair":d["required_repair"],
   "s083_imports_birth_filter":s["s083_imports_birth_filter"],"s083_calls_is_birth":s["s083_calls_is_birth"],
   "s083_continue_on_filter":s["s083_continue_on_filter"],"filter_family_terms":s["filter_family_terms"],
   "live_error":l["error"],"live_return_shape":l["return_shape"],
   "artifact_exists":l["artifact_exists"],"artifact_shape":l["artifact_shape"],
   "elapsed_seconds":round(l["elapsed_seconds"],3)},sort_keys=True))
  self.assertTrue(s["s083_exists"],"SULS083_MISSING")
  self.assertTrue(s["filter_exists"],"SULS076_FILTER_MISSING")
  self.assertTrue(s["s083_imports_birth_filter"],"SULS083_FILTER_IMPORT_NOT_FOUND")
  self.assertTrue(s["s083_calls_is_birth"],"SULS083_FILTER_CALL_NOT_FOUND")
  self.assertIsNone(l["error"],"UNIVERSAL_14_PROGRAM_PROBE_FAILED")
  self.assertFalse(d["certification_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-106O scanner birth-admission filter truth audit")
  print("[PASS] filtered SULS-083 lane distinguished from universal raw scanner admission")
  print("[PASS] no lifecycle certification claimed")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()

import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_161e_phase8_live_decoder_callable_certification import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT)
  summary={f:(None if x is None else {
   "module":x["module"],"function":x["function"],
   "signature":x["runtime_signature"],"score":x["score"]})
   for f,x in d["selected_callable_by_family"].items()}
  print("[STATE]",json.dumps({"ready_family_count":d["ready_family_count"],
   "ready_families":d["ready_families"],
   "importable_module_hits":d["importable_module_hits"],
   "callable_function_hits":d["callable_function_hits"],
   "selected":summary,"next_boundary":d["next_boundary"]},sort_keys=True))
  self.assertGreater(d["ready_family_count"],0,"NO_IMPORTABLE_CALLABLE_DECODER_INTERFACES")
  self.assertEqual(d["certification_semantics"],
   "IMPORT_AND_SIGNATURE_ONLY_NO_DECODER_INVOCATION")
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-161E live decoder callable certification")
  print("[PASS] callable imports + exact runtime signatures physically certified without invoking decoders")
  print("[NEXT]",d["next_boundary"])
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()

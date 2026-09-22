import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_106w_exact_birth_source_truth_audit import write
ROOT=Path(__file__).resolve().parent

class T(unittest.TestCase):
 def test_audit(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({
   "pump_source_count":d["pump_source_count"],
   "meteora_source_count":d["meteora_source_count"],
   "pump_candidate_callables":d["pump_candidate_callables"],
   "meteora_candidate_callables":d["meteora_candidate_callables"],
   "next_boundary":d["next_boundary"]},sort_keys=True))
  for group in ("pump_sources","meteora_sources"):
   for x in d[group]:
    print("[SOURCE]",x["path"])
    for y in x["interesting"]:print(f'{y["line"]}: {y["text"]}')
  self.assertGreater(d["pump_source_count"],0,"NO_USLS_020_024_PUMP_SOURCES_FOUND")
  self.assertGreater(d["meteora_source_count"],0,"NO_SULS_067_METEORA_SOURCES_FOUND")
  self.assertGreater(len(d["meteora_candidate_callables"]),0,"NO_METEORA_BIRTH_CALLABLE_FOUND")
  self.assertFalse(d["certification_claimed"])
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-106W exact birth source-truth audit")
  print("[PASS] Pump and Meteora existing birth pavement physically inspected")
  print("[NEXT] EXACT_BIRTH_DISPATCH_USING_VERIFIED_EXISTING_SOURCE_CONTRACTS")
  print("[PASS] execution_authority=FALSE")

if __name__=="__main__":unittest.main()

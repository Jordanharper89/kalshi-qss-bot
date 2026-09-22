import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_106v_exact_birth_decoder_interface_census import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_census(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({"candidate_module_count":d["candidate_module_count"],
   "exact_candidate_module_count":d["exact_candidate_module_count"],
   "family_module_counts":d["family_module_counts"],
   "next_boundary":d["next_boundary"]},sort_keys=True))
  for x in d["candidates"]:
   print("[CANDIDATE]",json.dumps(x,sort_keys=True))
  self.assertGreater(d["candidate_module_count"],0,"NO_BIRTH_DECODER_SOURCE_CANDIDATES")
  self.assertGreater(d["exact_candidate_module_count"],0,"NO_EXACT_BIRTH_DECODER_INTERFACES_DISCOVERED")
  self.assertFalse(d["certification_claimed"])
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-106V exact birth-decoder interface census")
  print("[PASS] existing decoder pavement inventoried without inventing interfaces")
  print("[NEXT] EXACT_BIRTH_DECODER_DISPATCH_FROM_DISCOVERED_INTERFACES")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()

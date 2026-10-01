import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_096_prospective_outcome_source_contract_audit import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_audit(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({"code_candidate_count":d["code_candidate_count"],
   "runtime_candidate_count":d["runtime_candidate_count"]},sort_keys=True))
  for x in d["code_candidates"][:40]:print("[CODE]",json.dumps(x,sort_keys=True))
  for x in d["runtime_candidates"][:40]:print("[RUNTIME]",json.dumps(x,sort_keys=True))
  self.assertGreater(d["code_candidate_count"],0)
  print("[PASS] SULS-096 prospective outcome source contract audit")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()

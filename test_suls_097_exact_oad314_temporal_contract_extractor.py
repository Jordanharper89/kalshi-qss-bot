import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_097_exact_oad314_temporal_contract_extractor import write
ROOT=Path(__file__).resolve().parent

class T(unittest.TestCase):
 def test_contract(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({"revision":d["revision"],
   "files":{k:v.get("exists") for k,v in d["contracts"].items()}},sort_keys=True))
  for name,x in d["contracts"].items():
   print("[CONTRACT]",name,json.dumps(x,sort_keys=True)[:12000])
  required=("oad314_callable_interface.json",
            "oad314_case_record_contract.json",
            "oad314_runtime_callables.json",
            "temporal_runtime_callables.json")
  for name in required:
   self.assertTrue(d["contracts"][name].get("exists"),name)
  print("[PASS] SULS-097 exact OAD-314 / temporal contract extractor")
  print("[PASS] execution_authority=FALSE")

if __name__=="__main__":unittest.main()

import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_069_no_future_leakage_certification import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_physical(self):
  p,d=write(ROOT);self.assertFalse(d["execution_authority"])
  print("[CASE_COUNT]",d["case_count"])
  for x in d["rows"]:print("[CHECK]",json.dumps(x,sort_keys=True))
  print("[NO_FUTURE_LEAKAGE_CERTIFIED]",d["no_future_leakage_certified"])
  if not d["no_future_leakage_certified"]:self.fail("FUTURE_DATA_LEAKAGE_OR_HORIZON_VIOLATION")
  print("[PASS] OSI-069 no-future-leakage certification")
if __name__=="__main__":unittest.main()

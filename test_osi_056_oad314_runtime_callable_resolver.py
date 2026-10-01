import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_056_oad314_runtime_callable_resolver import resolve,write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_physical(self):
  d=resolve();p=write(ROOT);self.assertGreater(d["callable_count"],0)
  print("[CALLABLE_COUNT]",d["callable_count"])
  for x in d["callables"][:20]:print("[CALLABLE]",json.dumps(x,sort_keys=True))
  print("[PASS] OSI-056 OAD-314 runtime callable resolver")
  print("[TRADER] Identifies the exact function OSI should reuse for future-result grading")
if __name__=="__main__":unittest.main()

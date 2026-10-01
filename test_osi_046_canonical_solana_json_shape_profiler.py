import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_046_canonical_solana_json_shape_profiler import profile,write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_physical(self):
  d=profile(ROOT);p=write(ROOT);self.assertGreater(d["rows_profiled"],0);self.assertTrue(d["profiles"])
  print("[ROWS_PROFILED]",d["rows_profiled"]);print("[OBSERVATION_TYPES]",sorted(d["profiles"]))
  for k in sorted(d["profiles"])[:6]:print("[PROFILE]",k,json.dumps(d["profiles"][k][:12],sort_keys=True))
  print("[PASS] OSI-046 canonical Solana JSON shape profiler")
  print("[TRADER] Shows the exact fields Oracle has actually scraped before formulas are defined")
if __name__=="__main__":unittest.main()

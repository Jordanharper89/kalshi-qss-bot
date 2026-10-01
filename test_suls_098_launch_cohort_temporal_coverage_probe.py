import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_098_launch_cohort_temporal_coverage_probe import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_probe(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({k:v for k,v in d.items() if k!="rows"},sort_keys=True))
  for r in d["rows"][:40]:print("[ROW]",json.dumps(r,sort_keys=True))
  self.assertGreater(d["event_count"],0)
  print("[PASS] SULS-098 launch-cohort temporal coverage probe")
  print("[SCOPE] Diagnostic only; zero coverage is a valid physical result")
if __name__=="__main__":unittest.main()

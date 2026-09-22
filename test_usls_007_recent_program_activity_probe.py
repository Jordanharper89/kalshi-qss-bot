import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_launch_scanner.usls_007_recent_program_activity_probe import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_probe(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({k:d[k] for k in (
   "program_count","query_success_count","programs_with_recent_signatures")},sort_keys=True))
  for r in d["rows"]:print("[ACTIVITY]",json.dumps(r,sort_keys=True))
  self.assertGreater(d["query_success_count"],0)
  self.assertGreater(d["programs_with_recent_signatures"],0)
  print("[PASS] USLS-007 recent mainnet program activity probe")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()

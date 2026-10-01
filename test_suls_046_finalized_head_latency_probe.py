import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_046_finalized_head_latency_probe import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_probe(self):
  p,d=write(ROOT);print("[STATE]",json.dumps(d,sort_keys=True))
  if not d.get("ok"):self.fail("FINALIZED_HEAD_LATENCY_PROBE_FAILED")
  print("[PASS] SULS-046 finalized-head latency probe")
  print("[TRADER] <=5s means finalized can serve launch entry timing; >5s means finalized is confirmation-only")
if __name__=="__main__":unittest.main()

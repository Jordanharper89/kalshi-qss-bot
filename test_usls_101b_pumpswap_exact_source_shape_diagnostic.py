import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_101b_pumpswap_exact_source_shape_diagnostic import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_diag(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({"candidate_count":d["candidate_count"]},sort_keys=True))
  for x in d["candidates"]:print("[SOURCE]",json.dumps(x,sort_keys=True))
  self.assertGreater(d["candidate_count"],0)
  self.assertFalse(d["certification_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-101B PumpSwap exact-source shape diagnostic")
  print("[PASS] no semantic certification claimed")
if __name__=="__main__":unittest.main()

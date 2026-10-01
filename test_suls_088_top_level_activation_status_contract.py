import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_088_top_level_activation_status_contract import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_contract(self):
  p,d=write(ROOT);print("[STATE]",json.dumps(d,sort_keys=True))
  self.assertTrue(d["suls_status_found"])
  self.assertGreaterEqual(d["suls_ack_count"],2)
  print("[PASS] SULS-088 top-level activation/status contract")
  print("[SCOPE]",d["scope"])
if __name__=="__main__":unittest.main()

import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_074_confirmed_logs_subscription_contract import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_contract(self):
  p,d=write(ROOT);print("[STATE]",json.dumps(d,sort_keys=True))
  self.assertEqual(len(d["subscriptions"]),2)
  self.assertTrue(all(x["method"]=="logsSubscribe" for x in d["subscriptions"]))
  self.assertTrue(all(x["params"][1]["commitment"]=="confirmed" for x in d["subscriptions"]))
  print("[PASS] SULS-074 confirmed logsSubscribe contract")
if __name__=="__main__":unittest.main()

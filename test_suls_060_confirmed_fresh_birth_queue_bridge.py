import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_060_confirmed_fresh_birth_queue_bridge import run,H
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_queue(self):
  d=run(ROOT);print("[STATE]",json.dumps({"admitted_fresh_births":d["admitted_fresh_births"],"pending_count":d["pending_count"]},sort_keys=True))
  self.assertEqual(list(H),[1,5,15,30,60,300,900])
  print("[PASS] SULS-060 confirmed fresh-birth queue bridge")
if __name__=="__main__":unittest.main()

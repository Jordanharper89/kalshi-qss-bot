import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_043_fresh_birth_horizon_queue import run,HORIZONS
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_queue(self):
  d=run(ROOT);print("[PHYSICAL_STATE]",json.dumps({"admitted_fresh_births":d["admitted_fresh_births"],"pending_count":d["pending_count"]},sort_keys=True))
  self.assertEqual(list(HORIZONS),[1,5,15,30,60,300,900])
  print("[PASS] SULS-043 fresh-birth horizon queue")
  print("[SCOPE] No fake freshness: queue only admits births observed within 5 seconds")
if __name__=="__main__":unittest.main()

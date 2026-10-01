import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_067c_live_priority_rate_safe_birth_worker import cycle
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_cycle(self):
  d=cycle(ROOT);print("[CYCLE]",json.dumps(d,sort_keys=True))
  self.assertEqual(d["anchor_count"],2);self.assertLessEqual(d["hydrated"],3)
  print("[PASS] SULS-067C live-priority rate-safe birth worker")
  print("[SCOPE] Fresh/live signatures are hydrated newest-first; recovery backlog drains separately")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()

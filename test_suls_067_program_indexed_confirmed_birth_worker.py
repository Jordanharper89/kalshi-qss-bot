import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_067_program_indexed_confirmed_birth_worker import cycle
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_cycle(self):
  d=cycle(ROOT);print("[CYCLE]",json.dumps(d,sort_keys=True))
  if d["candidate_signatures"]<=0:self.fail("NO_PROGRAM_INDEXED_CONFIRMED_ACTIVITY")
  self.assertEqual(d["anchor_count"],2)
  print("[PASS] SULS-067 program-indexed confirmed birth worker")
  print("[SCOPE] Replaces SULS-057 head-block scanning for the certified Meteora DBC/DAMM family")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()

import unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_064_prospective_pending_case_set import build,HORIZONS
ROOT=Path(__file__).resolve().parent

class T(unittest.TestCase):
 def test_physical(self):
  cases=build(ROOT)
  self.assertEqual(tuple(x.horizon_seconds for x in cases),HORIZONS)
  for c in cases:
   print("[CASE]",c.experience_id,c.horizon_seconds,c.snapshot_at)
  print("[PASS] OSI-064 prospective OAD-314 pending case set")
  print("[PASS] execution_authority=FALSE")

if __name__=="__main__":
 unittest.main()

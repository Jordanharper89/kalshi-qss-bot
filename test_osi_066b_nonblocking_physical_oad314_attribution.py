import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_066_physical_oad314_forward_outcome_attribution import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_physical(self):
  p,d=write(ROOT);self.assertFalse(d["execution_authority"])
  print("[RECORD_COUNT]",d["record_count"]);print("[VERIFIED_OUTCOMES]",d["verified_outcomes"]);print("[RESOLVED_HORIZONS]",d["resolved_horizons"])
  for x in d["outcomes"]:print("[OUTCOME]",json.dumps(x,sort_keys=True))
  if d["verified_outcomes"]==0:self.fail("OAD314_PRODUCED_NO_REAL_NONBLOCKING_OUTCOMES")
  print("[PASS] OSI-066B physical OAD-314 attribution from nonblocking native records")
  print("[TRADER] OAD-314 graded real future prices against the exact prospective anchor")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()

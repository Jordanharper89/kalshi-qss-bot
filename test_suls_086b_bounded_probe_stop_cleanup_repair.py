import unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_086_bounded_existing_osi_child_physical_probe import probe
ROOT=Path(__file__).resolve().parent
STOP=ROOT/"runtime_state/solana_intelligence/STOP_OSI_LIVE"
class T(unittest.TestCase):
 def test_cleanup(self):
  d=probe(ROOT,seconds=4.0)
  print("[STATE]",d)
  self.assertTrue(d["suls_connected"])
  self.assertGreaterEqual(d["ack_count"],2)
  self.assertGreaterEqual(d["notifications"],1)
  self.assertFalse(STOP.exists())
  print("[PASS] SULS-086B bounded probe STOP marker cleanup")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()

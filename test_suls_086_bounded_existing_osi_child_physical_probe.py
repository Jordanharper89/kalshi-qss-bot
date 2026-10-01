import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_086_bounded_existing_osi_child_physical_probe import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_probe(self):
  p,d=write(ROOT);print("[STATE]",json.dumps(d,sort_keys=True))
  if not d["status_found"] or not d["suls_connected"] or d["ack_count"]<2 or d["notifications"]<1:
   self.fail("BOUND_OSI_CHILD_SULS_NOT_PHYSICAL")
  print("[PASS] SULS-086 bounded existing OSI child physical probe")
  print("[SCOPE] Bounded child launch only; top-level Oracle launcher not started")
if __name__=="__main__":unittest.main()

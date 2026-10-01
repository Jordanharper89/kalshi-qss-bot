import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_033_canonical_tradeable_native_birth_event import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_event(self):
  p,d=write(ROOT);print("[EVENT_COUNT]",d["event_count"])
  for e in d["events"]:print("[TRADEABLE_BIRTH_EVENT]",json.dumps(e,sort_keys=True))
  if d["event_count"]==0:self.fail("NO_CANONICAL_NATIVE_BIRTH_EVENT")
  print("[PASS] SULS-033 canonical tradeable native birth event")
if __name__=="__main__":unittest.main()

import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_037_native_lifecycle_snapshot_normalizer import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_norm(self):
  p,d=write(ROOT);print("[SNAPSHOT_COUNT]",d["snapshot_count"])
  for x in d["snapshots"]:print("[LIFECYCLE_SNAPSHOT]",json.dumps(x,sort_keys=True))
  if not d["snapshots"]:self.fail("NO_LIFECYCLE_SNAPSHOT")
  if not any(x.get("quote_per_token") for x in d["snapshots"]):self.fail("NO_NATIVE_RATIO")
  print("[PASS] SULS-037 native lifecycle snapshot normalizer")
if __name__=="__main__":unittest.main()

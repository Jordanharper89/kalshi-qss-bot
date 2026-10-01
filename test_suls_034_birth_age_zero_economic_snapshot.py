import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_034_birth_age_zero_economic_snapshot import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_snapshot(self):
  p,d=write(ROOT);print("[SNAPSHOT_COUNT]",d["snapshot_count"])
  for x in d["snapshots"]:print("[AGE_ZERO]",json.dumps(x,sort_keys=True))
  if d["snapshot_count"]==0:self.fail("NO_AGE_ZERO_SNAPSHOT")
  if not any(x.get("initial_quote_per_token") for x in d["snapshots"]):self.fail("NO_NATIVE_INITIAL_PRICE_RATIO")
  print("[PASS] SULS-034 birth age-zero economic snapshot")
if __name__=="__main__":unittest.main()

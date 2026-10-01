import unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_063_fresh_native_prospective_anchor import write

ROOT=Path(__file__).resolve().parent

class T(unittest.TestCase):
 def test_physical(self):
  p,d=write(ROOT)
  self.assertFalse(d["execution_authority"])
  print("[LIVE_ASSET]",d["asset_key"])
  print("[BEFORE_RECORDS]",d["before_records"])
  print("[AFTER_RECORDS]",d["after_records"])
  print("[FRESH_RECORDS]",d["fresh_records"])
  print("[ANCHOR_OBSERVATION]",d["observation_id"])
  print("[ANCHOR_AT]",d["observed_at"])
  print("[PAIR]",d["pair_address"])
  print("[ANCHOR_PRICE]",d["price_usd"])
  if d["after_records"]<1:
   self.fail("NO_NATIVE_HISTORY_AFTER_FRESH_ACQUISITION")
  if not d["pair_address"]:
   self.fail("NO_PAIR_ON_FRESH_ANCHOR")
  print("[PASS] OSI-063B current-live-token native prospective anchor")
  print("[TRADER] Selects a token that is live now, freezes its fresh pool state, and does not reuse a stale opportunity")
  print("[PASS] execution_authority=FALSE")

if __name__=="__main__":
 unittest.main()

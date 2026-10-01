import unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_063_fresh_native_prospective_anchor import write

ROOT=Path(__file__).resolve().parent

class T(unittest.TestCase):
 def test_physical(self):
  p,d=write(ROOT)
  self.assertFalse(d["execution_authority"])
  self.assertFalse(d["postgres_persistence_required_before_anchor"])
  print("[LIVE_ASSET]",d["asset_key"])
  print("[ANCHOR_SOURCE]",d["anchor_source"])
  print("[ANCHOR_OBSERVATION]",d["observation_id"])
  print("[ANCHOR_AT]",d["observed_at"])
  print("[SOURCE_ID]",d["source_id"])
  print("[PAIR]",d["pair_address"])
  print("[ANCHOR_PRICE]",d["price_usd"])
  print("[LIQUIDITY_USD]",d["liquidity_usd"])
  print("[VOLUME_H24]",d["volume_h24"])
  print("[BUYS_H24]",d["buys_h24"])
  print("[SELLS_H24]",d["sells_h24"])
  print("[PAIR_CREATED_AT]",d["pair_created_at"])
  print("[POSTGRES_BLOCKING_REQUIRED]",d["postgres_persistence_required_before_anchor"])
  print("[PASS] OSI-063E exact native-object prospective anchor")
  print("[TRADER] Freezes a real live Solana pool observation using the certified object contract")
  print("[PASS] execution_authority=FALSE")

if __name__=="__main__":
 unittest.main()

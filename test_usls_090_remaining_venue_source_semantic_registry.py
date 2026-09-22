import unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_090_remaining_venue_source_semantic_registry import *
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_registry(self):
  p,d=write(ROOT)
  self.assertEqual(SEMANTICS["MOONIT"]["66063d1201daebea"]["side"],"BUY")
  self.assertEqual(SEMANTICS["MOONIT"]["33e685a4017f83ad"]["side"],"SELL")
  self.assertEqual(SEMANTICS["BOOP_FUN"]["8a7f0e5b26577369"]["side"],"BUY")
  self.assertEqual(SEMANTICS["BOOP_FUN"]["6d3d28bbe6b087ae"]["side"],"SELL")
  self.assertEqual(SEMANTICS["HEAVEN"]["66063d1201daebea"]["side"],"BUY")
  self.assertEqual(SEMANTICS["HEAVEN"]["33e685a4017f83ad"]["side"],"SELL")
  self.assertTrue(d["unknown_retention"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-090 source-backed Moonit/Boop/Heaven trade semantics")
  print("[PASS] physical USLS-088 fingerprints mapped without dropping unknown instructions")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()

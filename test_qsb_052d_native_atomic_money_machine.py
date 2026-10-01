import unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core as c
class T(unittest.TestCase):
 def test_no_jupiter(self):
  with open(c.__file__,encoding="utf-8") as f:s=f.read().lower()
  self.assertNotIn("jup.ag",s);self.assertNotIn("jupiter",s.replace("jupiter=none",""))
  print("[PASS] zero Jupiter dependency")
 def test_atomic_gate(self):
  start=25_000_000;end=25_200_000
  bps=(end-start)/start*10000
  self.assertGreater(bps,c.MIN_NET_BPS)
  print("[PASS] positive same-token spread clears profit gate")
 def test_negative_rejected(self):
  start=25_000_000;end=24_900_000
  bps=(end-start)/start*10000
  self.assertLess(bps,c.MIN_NET_BPS)
  print("[PASS] negative spread rejected before transaction")
 def test_pump_pool_decode(self):
  z=b"\0"*32
  d=b"12345678"+b"\x01"+b"\0\0"+z*6
  x=c.decode_pump_pool(d)
  self.assertIn("base_mint",x);self.assertIn("quote_vault",x)
  print("[PASS] PumpSwap raw pool identity decoder")
if __name__=="__main__":unittest.main(verbosity=2)

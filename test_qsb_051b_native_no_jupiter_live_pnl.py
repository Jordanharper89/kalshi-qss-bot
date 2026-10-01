import struct,unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.native_no_jupiter_live_pnl import core as c
def b58d(s):
 n=0
 for ch in s:n=n*58+c.ALPH.index(ch)
 b=n.to_bytes((n.bit_length()+7)//8,"big") if n else b""
 return b"\0"*(len(s)-len(s.lstrip("1")))+b
class T(unittest.TestCase):
 def test_pump_pool_layout(self):
  keys=["11111111111111111111111111111111"]*6
  d=b"12345678"+bytes([1])+struct.pack("<H",0)+b"".join(b58d(x) for x in keys)+struct.pack("<Q",100)+b58d(keys[0])+bytes([0,0])+int(0).to_bytes(16,"little",signed=True)
  x=c.decode_pump_pool(d);self.assertEqual(x["index"],0);self.assertEqual(x["lp_supply"],100)
  print("[PASS] PumpSwap Pool raw layout decoded locally")
 def test_cpmm_sell(self):
  old1,old2=c.account_bytes,c.token_amount
  # pool: base/quote both dummy; use WSOL quote
  z=b58d("11111111111111111111111111111111")
  w=b58d(c.WSOL)
  d=b"12345678"+bytes([1])+struct.pack("<H",0)+z+z+w+z+z+z+struct.pack("<Q",1)+z+bytes([0,0])+int(0).to_bytes(16,"little",signed=True)
  c.account_bytes=lambda a:d
  vals=iter([1_000_000,1_000_000_000]);c.token_amount=lambda a:next(vals)
  try:
   x=c.pump_sell_quote("P",10000);self.assertGreater(x["raw_out"],0)
  finally:c.account_bytes,c.token_amount=old1,old2
  print("[PASS] PumpSwap CPMM quote is local; no quote API")
 def test_no_jupiter_source(self):
  s=open(c.__file__,encoding="utf-8").read().lower()
  self.assertNotIn("jup.ag",s);self.assertNotIn("/quote?",s);self.assertNotIn("swap-instructions",s)
  print("[PASS] zero Jupiter hot-path code")
if __name__=="__main__":unittest.main(verbosity=2)

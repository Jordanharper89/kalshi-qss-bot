import base64,struct,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_045b_universal_multidex_decoder_framework import *
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_framework(self):
  p,d=write(ROOT);self.assertEqual(len(d["programs"]),14)
  raw=PS_BUY+struct.pack("<q"+"Q"*13,1,*range(2,15))+b"\0"*64
  x=route("PUMP_SWAP","Program data: "+base64.b64encode(raw).decode())
  self.assertEqual(x["decode_status"],"EXACT");self.assertEqual(x["event"]["side"],"BUY")
  y=route("RAYDIUM_V4","Program log: swap")
  self.assertEqual(y["decode_status"],"RAW_RETAINED_DECODER_PENDING")
  self.assertTrue(d["unknown_retention"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-045B universal multi-DEX decoder framework")
  print("[PASS] PumpSwap exact plugin migrated into shared framework")
  print("[PASS] undecoded venues retained raw, never dropped or guessed")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()

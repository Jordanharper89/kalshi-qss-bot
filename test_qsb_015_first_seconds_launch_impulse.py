import tempfile,unittest,time
from pathlib import Path
from qseries_v2.solana_qsb015_first_seconds import FirstSecondsLane
class T(unittest.TestCase):
 def test_first_seconds_entry_without_long_history(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);lane=FirstSecondsLane(root)
   burst={"hot_mints":[{"mint":"MEME1","signature_hits":2}]}
   rows=[{"market_address":"POOL1","token_mint":"MEME1","family":"RAYDIUM_CPMM","last_price":1.0,
          "liquidity_usd":10000,"volume_usd":5000,"buy_count":10,"sell_count":2}]
   e=lane.evaluate(burst,rows)
   self.assertEqual(len(e),1);self.assertEqual(e[0]["strategy"],"FIRST_SECONDS_LAUNCH_IMPULSE")
   self.assertEqual(e[0]["family"],"RAYDIUM_CPMM")
   print("[PASS] QSB-015 enters first-seconds CPMM paper trade without waiting for long price history")
if __name__=="__main__":unittest.main()

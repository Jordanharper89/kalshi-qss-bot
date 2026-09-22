import unittest
from qseries_v2.oracle_adapters.independent.oad_254_solana_dex_liquidity_intelligence import *
class T(unittest.TestCase):
 def test_dex(self):
  def f(url,timeout): return {"pairs":[{"chainId":"solana","dexId":"x","pairAddress":"p","baseToken":{"address":"b"},"quoteToken":{"address":"q"},"priceUsd":"1","liquidity":{"usd":1000},"volume":{"h24":500},"txns":{"h24":{"buys":2,"sells":1}}}]}
  x=acquire_solana_dex_liquidity(fetch=f); print("[PAIRS]",x.payload["pair_count"]); self.assertEqual(x.payload["pair_count"],1)
if __name__=="__main__":
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful(): raise SystemExit(1)
 print("[PASS] OAD-254 Solana DEX liquidity intelligence certified")

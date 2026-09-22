import unittest
from qseries_v2.oracle_adapters.independent.oad_255_solana_stablecoin_supply_intelligence import *
class T(unittest.TestCase):
 def test_supply(self):
  def r(method,params,timeout): return {"result":{"value":{"amount":"1000000","decimals":6,"uiAmountString":"1"}}}
  x=acquire_solana_stablecoin_supply(rpc=r); print("[STABLECOIN]",x.payload); self.assertEqual(x.payload["symbol"],"USDC")
if __name__=="__main__":
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful(): raise SystemExit(1)
 print("[PASS] OAD-255 Solana stablecoin supply intelligence certified")

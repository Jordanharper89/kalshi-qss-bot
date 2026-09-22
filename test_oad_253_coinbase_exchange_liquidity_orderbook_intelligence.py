import unittest
from qseries_v2.oracle_adapters.independent.oad_253_coinbase_exchange_liquidity_orderbook_intelligence import *
class T(unittest.TestCase):
 def test_book(self):
  def f(url,timeout): return {"sequence":9,"bids":[["100","2",1]],"asks":[["101","3",1]]}
  x=acquire_coinbase_orderbook(fetch=f); print("[BOOK]",x.payload); self.assertEqual(x.payload["spread"],1.0)
if __name__=="__main__":
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful(): raise SystemExit(1)
 print("[PASS] OAD-253 Coinbase order-book intelligence certified")

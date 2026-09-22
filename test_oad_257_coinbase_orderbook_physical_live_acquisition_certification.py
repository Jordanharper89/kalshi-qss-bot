import unittest
from qseries_v2.oracle_adapters.independent.oad_257_coinbase_orderbook_physical_live_acquisition_certification import *
class T(unittest.TestCase):
 def test_physical(self):
  r=certify_live_coinbase_orderbook()
  print("[PHYSICAL] product=",r.product_id); print("[PHYSICAL] bid=",r.best_bid,"ask=",r.best_ask,"spread=",r.spread); print("[PHYSICAL] levels=",r.bid_levels,r.ask_levels); print("[PHYSICAL] provider=",r.provider)
  self.assertTrue(r.certified); self.assertFalse(r.execution_authority)
if __name__=="__main__":
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful(): raise SystemExit(1)
 print("[PASS] OAD-257 physical live Coinbase order-book acquisition certified")

\

import unittest
from types import SimpleNamespace
from qseries_v2.oracle_adapters.independent.oad_329_solana_dex_transaction_attribution import *
class T(unittest.TestCase):
 def test_attribution(self):
  reg=SimpleNamespace(by_pair=(("POOL","raydium"),))
  e=SimpleNamespace(signature="s",slot=1,account_keys=("A","POOL","B"))
  x=attribute_transactions_to_live_dex_pools((e,),reg)[0]
  print("[ATTR]",x.signature,x.dex_ids,x.matched_pool_accounts)
  self.assertTrue(x.attributed);self.assertEqual(x.dex_ids,("raydium",))
if __name__=="__main__":
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful():raise SystemExit(1)
 print("[PASS] OAD-329 live DEX transaction attribution certified")


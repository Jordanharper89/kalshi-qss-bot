\

import unittest
from types import SimpleNamespace
from qseries_v2.oracle_adapters.independent.oad_331_solana_dex_market_behavior_inference import *
class T(unittest.TestCase):
 def test_swap(self):
  e=SimpleNamespace(signature="s",slot=1)
  a=SimpleNamespace(signature="s",attributed=True,dex_ids=("orca",),matched_pool_accounts=("P",))
  f=(SimpleNamespace(signature="s",owner="W",mint="A",delta=-2.0),SimpleNamespace(signature="s",owner="W",mint="B",delta=5.0))
  x=infer_solana_market_behavior((e,),(a,),f)[0]
  print("[BEHAVIOR]",x.behavior,x.dex_ids,x.mints)
  self.assertEqual(x.behavior,"DEX_SWAP")
if __name__=="__main__":
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful():raise SystemExit(1)
 print("[PASS] OAD-331 evidence-grounded DEX swap/liquidity behavior inference certified")


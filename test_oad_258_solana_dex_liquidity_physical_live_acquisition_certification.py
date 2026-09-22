import unittest
from qseries_v2.oracle_adapters.independent.oad_258_solana_dex_liquidity_physical_live_acquisition_certification import *
class T(unittest.TestCase):
 def test_physical(self):
  r=certify_live_solana_dex_liquidity()
  print("[PHYSICAL] query=",r.query); print("[PHYSICAL] pair_count=",r.pair_count); print("[PHYSICAL] dex_ids=",r.dex_ids); print("[PHYSICAL] first_pair=",r.pair_addresses[0])
  self.assertGreater(r.pair_count,0); self.assertTrue(r.certified)
if __name__=="__main__":
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful(): raise SystemExit(1)
 print("[PASS] OAD-258 physical live Solana DEX liquidity acquisition certified")

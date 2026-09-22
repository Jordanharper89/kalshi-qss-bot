import unittest
from qseries_v2.oracle_adapters.independent.oad_259_solana_stablecoin_physical_live_acquisition_certification import *
class T(unittest.TestCase):
 def test_physical(self):
  r=certify_live_solana_stablecoin_supply("USDC")
  print("[PHYSICAL] symbol=",r.symbol); print("[PHYSICAL] mint=",r.mint); print("[PHYSICAL] amount_raw=",r.amount_raw); print("[PHYSICAL] decimals=",r.decimals)
  self.assertEqual(r.symbol,"USDC"); self.assertTrue(r.certified)
if __name__=="__main__":
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful(): raise SystemExit(1)
 print("[PASS] OAD-259 physical live finalized Solana USDC supply certified")

\

import unittest
from unittest.mock import patch
from types import SimpleNamespace
from qseries_v2.oracle_adapters.independent import oad_328_solana_live_dex_pool_identity_registry as m
class T(unittest.TestCase):
 def test_registry(self):
  obs=SimpleNamespace(provider="dexscreener",payload={"pairs":[{"pair_address":"P1","dex_id":"raydium"},{"pair_address":"P2","dex_id":"orca"},{"pair_address":"P3","dex_id":"meteora"},{"pair_address":"P4","dex_id":"pumpswap"}]})
  with patch.object(m,"acquire_solana_dex_liquidity",return_value=obs):
   x=m.build_live_solana_dex_pool_registry()
  print("[DEXES]",x.dexes,"pools=",x.pools)
  self.assertEqual(x.pools,4);self.assertIn("raydium",x.dexes);self.assertIn("pumpswap",x.dexes)
if __name__=="__main__":
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful():raise SystemExit(1)
 print("[PASS] OAD-328 live Solana DEX/pool identity registry certified")


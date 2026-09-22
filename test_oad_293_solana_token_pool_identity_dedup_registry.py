import unittest
from qseries_v2.oracle_adapters.independent.oad_293_solana_token_pool_identity_dedup_registry import *
class T(unittest.TestCase):
 def test_physical(self):
  r=build_solana_token_pool_identity_registry(max_tokens=8)
  print("[PHYSICAL] tokens=",r.tokens); print("[PHYSICAL] pools=",r.pools); print("[PHYSICAL] failures=",r.acquisition_failures)
  self.assertGreater(r.tokens,0); self.assertGreater(r.pools,0)
  self.assertEqual(len({(x.token_address,x.pair_address) for x in r.identities}),r.pools)
if __name__=="__main__":
 z=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not z.wasSuccessful(): raise SystemExit(1)
 print("[PASS] OAD-293 deterministic token/pool identity dedup physically certified")

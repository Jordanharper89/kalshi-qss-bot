import unittest
from qseries_v2.oracle_adapters.independent.oad_263_solana_token_pool_identity_liquidity_expansion import *
class T(unittest.TestCase):
 def test_physical(self):
  o=expand_live_solana_token_pools(); p=o.payload["pools"][0]; print("[PHYSICAL] token=",o.payload["token_address"]); print("[PHYSICAL] pool_count=",o.payload["pool_count"]); print("[PHYSICAL] first_pool=",p["pair_address"],p["dex_id"],p["base_symbol"],p["quote_symbol"]); self.assertGreater(o.payload["pool_count"],0)
if __name__=="__main__":
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful(): raise SystemExit(1)
 print("[PASS] OAD-263 live Solana token/pool identity and liquidity expansion certified")

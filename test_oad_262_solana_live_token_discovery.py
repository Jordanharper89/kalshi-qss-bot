import unittest
from qseries_v2.oracle_adapters.independent.oad_262_solana_live_token_discovery import *
class T(unittest.TestCase):
 def test_physical(self):
  o=discover_live_solana_tokens(); print("[PHYSICAL] token_count=",o.payload["token_count"]); print("[PHYSICAL] first_token=",o.payload["tokens"][0]["token_address"]); print("[PHYSICAL] endpoint_failures=",o.payload["endpoint_failures"]); self.assertGreater(o.payload["token_count"],0)
if __name__=="__main__":
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful(): raise SystemExit(1)
 print("[PASS] OAD-262 live Solana token discovery physically certified")

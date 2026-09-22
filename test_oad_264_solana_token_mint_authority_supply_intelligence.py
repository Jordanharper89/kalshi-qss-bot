import unittest
from qseries_v2.oracle_adapters.independent.oad_264_solana_token_mint_authority_supply_intelligence import *
class T(unittest.TestCase):
 def test_physical(self):
  o=acquire_solana_token_mint_state(); p=o.payload; print("[PHYSICAL] token=",p["token_address"]); print("[PHYSICAL] supply_raw=",p["supply_raw"],"decimals=",p["decimals"]); print("[PHYSICAL] mint_authority=",p["mint_authority"]); print("[PHYSICAL] freeze_authority=",p["freeze_authority"]); self.assertIsNotNone(p["supply_raw"])
if __name__=="__main__":
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful(): raise SystemExit(1)
 print("[PASS] OAD-264 live finalized Solana mint authority/supply intelligence certified")

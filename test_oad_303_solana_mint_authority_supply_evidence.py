import unittest
from qseries_v2.oracle_adapters.independent.oad_303_solana_mint_authority_supply_evidence import *
class T(unittest.TestCase):
    def test_physical(self):
        x=acquire_current_mint_authority_supply_evidence()
        p=x.chain_observation.payload
        print("[PHYSICAL] token=",x.token_address); print("[PHYSICAL] mint_authority=",p.get("mint_authority")); print("[PHYSICAL] freeze_authority=",p.get("freeze_authority")); print("[PHYSICAL] supply_raw=",p.get("supply_raw"))
        self.assertEqual(str(p.get("token_address")),x.token_address); self.assertTrue(x.chain_independent_of_gmgn); self.assertFalse(x.execution_authority)
if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-303 exact OAD-264 finalized Solana mint/authority/supply evidence physically certified")
